from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceivedNote
from apps.purchasing.serializers import SupplierSerializer, PurchaseOrderSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().prefetch_related("lines__product")
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        Create a GRN from the PO lines.
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

        grn.save()

        # Update PO status
        if all(l.is_complete for l in po.lines.all()):
            po.status = "received"
        elif any(l.received_qty > 0 for l in po.lines.all()):
            po.status = "partial"
        po.save()

        return Response({"grn": grn.grn_number, "status": po.status})
