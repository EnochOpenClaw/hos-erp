from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from apps.purchasing.models import (
    Supplier, PurchaseOrder, PurchaseOrderLine,
    GoodsReceivedNote, GoodsReceivedNoteLine,
    PurchaseInvoice, PurchaseInvoiceLine, PurchasePriceHistory,
)
from apps.purchasing.serializers import (
    SupplierSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderApproveSerializer,
    GoodsReceivedNoteSerializer,
    PurchaseInvoiceSerializer,
    PurchasePriceHistorySerializer,
)
from apps.products.models import Product


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get_queryset(self):
        qs = Supplier.objects.filter(company__name="OpenFactory Systems")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().prefetch_related("lines__product")

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer

    def get_queryset(self):
        qs = PurchaseOrder.objects.filter(
            company__name="OpenFactory Systems"
        ).prefetch_related("lines")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(po_number__icontains=search)
        phase = self.request.query_params.get("phase")
        if phase:
            qs = qs.filter(phase=phase)
        reason = self.request.query_params.get("reason")
        if reason:
            qs = qs.filter(reason=reason)
        supplier = self.request.query_params.get("supplier")
        if supplier:
            qs = qs.filter(supplier_id=supplier)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        Approve a PO (move from pending_approval → approved).
        Body: { "approved_by": "John Smith", "is_eft": false }
        """
        po = self.get_object()
        serializer = PurchaseOrderApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po.phase = "approved"
        po.approved_by = serializer.validated_data["approved_by"]
        po.is_eft = serializer.validated_data.get("is_eft", False)
        po.approved_at = timezone.now()
        po.save()
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        Mark PO as sent to supplier (approved → ordered).
        """
        po = self.get_object()
        if po.phase != "approved":
            return Response(
                {"detail": "PO must be approved before sending"},
                status=status.HTTP_400_BAD_REQUEST
            )
        po.phase = "ordered"
        po.save()
        return Response(PurchaseOrderSerializer(po).data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        Create a GRN from the PO lines (ordered → partial/received).
        Body: { "lines": { "<po_line_id>": <received_qty>, ... }, "notes": "" }
        """
        po = self.get_object()
        data = request.data
        lines_data = data.get("lines", {})

        grn = GoodsReceivedNote.objects.create(
            company=po.company,
            po=po,
            notes=data.get("notes", ""),
        )

        for line in po.lines.all():
            qty = float(lines_data.get(str(line.id), 0))
            if qty > 0:
                line.received_qty += qty
                line.save()
                grn.lines.create(po_line=line, received_qty=qty)

        # Update PO phase
        if all(l.is_complete for l in po.lines.all()):
            po.phase = "received"
        elif any(l.received_qty > 0 for l in po.lines.all()):
            po.phase = "partial"
        po.save()
        grn.save()

        return Response({
            "grn": grn.grn_number,
            "phase": po.phase,
            "grn_id": str(grn.id),
        })

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a PO."""
        po = self.get_object()
        po.phase = "cancelled"
        po.save()
        return Response({"phase": po.phase})


class GoodsReceivedNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceivedNote.objects.all()
    serializer_class = GoodsReceivedNoteSerializer

    def get_queryset(self):
        qs = GoodsReceivedNote.objects.filter(company__name="OpenFactory Systems")
        po_id = self.request.query_params.get("po")
        if po_id:
            qs = qs.filter(po_id=po_id)
        return qs


class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    queryset = PurchaseInvoice.objects.all().prefetch_related("lines")
    serializer_class = PurchaseInvoiceSerializer

    def get_queryset(self):
        qs = PurchaseInvoice.objects.filter(company__name="OpenFactory Systems")
        po_id = self.request.query_params.get("po")
        if po_id:
            qs = qs.filter(po_id=po_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        """
        Post an invoice: run variance check, update stock, update selling prices.
        Lines must be supplied with actual invoiced qty and unit prices.
        Body: {
          "lines": [
            { "po_line": "<id>", "invoiced_qty": 10, "unit_price": "125.00" }
          ]
        }
        Returns variance report before saving.
        """
        invoice = self.get_object()
        if invoice.status == "posted":
            return Response({"detail": "Invoice already posted"}, status=status.HTTP_400_BAD_REQUEST)

        lines_data = request.data.get("lines", [])
        if not lines_data:
            return Response({"detail": "At least one line is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Build invoice lines and calculate variances
            variances = {}
            subtotal = 0

            for line_data in lines_data:
                po_line_id = str(line_data["po_line"])
                po_line = PurchaseOrderLine.objects.select_related("product").get(id=po_line_id)
                invoiced_qty = line_data["invoiced_qty"]
                unit_price = line_data["unit_price"]
                price_variance = float(unit_price) - float(po_line.unit_price)
                line_total = float(invoiced_qty) * float(unit_price)

                inv_line = PurchaseInvoiceLine.objects.create(
                    invoice=invoice,
                    po_line=po_line,
                    invoiced_qty=invoiced_qty,
                    unit_price=unit_price,
                    price_variance=price_variance,
                    line_total=line_total,
                )

                # Record price history
                PurchasePriceHistory.objects.create(
                    company=invoice.company,
                    product=po_line.product,
                    supplier=invoice.po.supplier,
                    unit_price=unit_price,
                    po_line=po_line,
                )

                # Update product unit_cost (latest purchase price)
                product = po_line.product
                product.unit_cost = unit_price

                # Auto-update selling price
                markup_pct = (
                    product.markup_override
                    or (product.category.default_markup_pct if product.category else 30)
                )
                product.selling_price = round(float(unit_price) * (1 + markup_pct / 100), 4)
                product.save()

                if price_variance != 0:
                    variances[po_line.product.code] = {
                        "product": po_line.product.name,
                        "old_price": str(po_line.unit_price),
                        "new_price": str(unit_price),
                        "variance": str(price_variance),
                        "variance_pct": f"{(price_variance / float(po_line.unit_price)) * 100:.1f}%",
                    }

                subtotal += line_total

            # Update PO line received qty
            for inv_line in invoice.lines.all():
                po_line = inv_line.po_line
                po_line.received_qty = invoiced_qty  # from last posted line
                po_line.save()

            # Calculate totals
            vat = subtotal * 0.15  # assuming 15% VAT
            total = subtotal + vat

            invoice.subtotal = subtotal
            invoice.vat = vat
            invoice.total = total
            invoice.price_variance_json = variances
            invoice.status = "posted"
            invoice.posted_by = request.data.get("posted_by", "")
            invoice.posted_at = timezone.now()
            invoice.save()

            # Update PO phase
            po = invoice.po
            if all(l.is_complete for l in po.lines.all()):
                po.phase = "received"
            elif any(l.received_qty > 0 for l in po.lines.all()):
                po.phase = "partial"
            po.save()

        return Response({
            "status": "posted",
            "subtotal": str(subtotal),
            "vat": str(vat),
            "total": str(total),
            "price_variances": variances,
        })


class PurchasePriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PurchasePriceHistory.objects.all()
    serializer_class = PurchasePriceHistorySerializer

    def get_queryset(self):
        qs = PurchasePriceHistory.objects.filter(company__name="OpenFactory Systems")
        product_id = self.request.query_params.get("product")
        if product_id:
            qs = qs.filter(product_id=product_id)
        supplier_id = self.request.query_params.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs