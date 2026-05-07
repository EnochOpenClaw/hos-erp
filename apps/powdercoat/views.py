# powdercoat/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .models import (
    PowdercoatJob, PowdercoatJobItem, PowdercoatSupplier,
    QualityCheck, StockIssue, StockIssueLine,
)
from .serializers import (
    PowdercoatJobSerializer, PowdercoatJobItemSerializer,
    PowdercoatSupplierSerializer, StockIssueSerializer,
    StockIssueLineSerializer, CreateQCCheckSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# QC Check ViewSet (standalone)
# ─────────────────────────────────────────────────────────────────────────────

class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.select_related("stock_item", "powdercoat_job").all()
    serializer_class = CreateQCCheckSerializer

    @action(detail=True, methods=["post"])
    def pass_check(self, request, pk=None):
        qc = self.get_object()
        qc.result = "pass"
        qc.save()
        return Response(QualityCheckSerializer(qc).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        qc = self.get_object()
        qc.result = "fail"
        qc.fail_reason = request.data.get("fail_reason", "")
        qc.notes = request.data.get("notes", "")
        qc.save()
        return Response(QualityCheckSerializer(qc).data)


# ─────────────────────────────────────────────────────────────────────────────
# PowdercoatSupplier ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class PowdercoatSupplierViewSet(viewsets.ModelViewSet):
    queryset = PowdercoatSupplier.objects.all()
    serializer_class = PowdercoatSupplierSerializer


# ─────────────────────────────────────────────────────────────────────────────
# PowdercoatJob ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class PowdercoatJobViewSet(viewsets.ModelViewSet):
    queryset = PowdercoatJob.objects.select_related("division", "supplier").all()
    serializer_class = PowdercoatJobSerializer

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/send/
        Transition items to 'sent_powder', create QC check outgoing.
        """
        job: PowdercoatJob = self.get_object()
        if job.status != "draft":
            return Response({"error": f"Cannot send from status '{job.status}'"}, status=400)

        with transaction.atomic():
            for item in job.items.select_related("stock_item").all():
                si = item.stock_item
                item.sent_state = si.state
                item.save(update_fields=["sent_state"])
                si.state = "sent_powder"
                si.save(update_fields=["state"])

            job.status = "sent"
            job.sent_date = request.data.get("send_date")
            job.save(update_fields=["status", "sent_date"])

        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/receive/
        Items are back from powder coater. Create incoming QC check.
        """
        job: PowdercoatJob = self.get_object()
        if job.status != "sent":
            return Response({"error": f"Cannot receive in status '{job.status}'"}, status=400)

        with transaction.atomic():
            for item in job.items.select_related("stock_item").all():
                item.returned_state = item.stock_item.state
                item.save(update_fields=["returned_state"])

            job.status = "returned"
            job.returned_date = request.data.get("return_date")
            job.save(update_fields=["status", "returned_date"])

        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/complete/
        All items received back with powder colour applied.
        Transitions each StockItem to 'returned_powder' with powder_color set.
        Items are now identity-changed: same extrusion + same colour only.

        Optional body: { "qc_pass": true/false }
          - If qc_pass=false, items marked 'conditional' but still returned_powder.
        """
        job: PowdercoatJob = self.get_object()
        if job.status != "returned":
            return Response({"error": f"Cannot complete in status '{job.status}'"}, status=400)

        qc_pass = request.data.get("qc_pass", True)
        colour  = job.powder_color or ""

        with transaction.atomic():
            for item in job.items.select_related("stock_item").all():
                si = item.stock_item

                # Bind colour to the stock item — it cannot be removed
                si.powder_color = colour
                si.finish = "powdercoated"
                si.state = "returned_powder"
                si.save(update_fields=["powder_color", "finish", "state"])

                # Snapshot the returned state on the line
                item.returned_state = si.state
                item.qc_result = "pass" if qc_pass else "conditional"
                item.save(update_fields=["returned_state", "qc_result"])

            job.status = "completed"
            job.save(update_fields=["status"])

        # Create a QC record for the completed job
        QualityCheck.objects.create(
            check_type="incoming_powdercoat",
            result="pass" if qc_pass else "conditional",
            powdercoat_job=job,
            checked_by=request.data.get("checked_by", ""),
            notes=request.data.get("notes", ""),
            condition=not qc_pass,
        )

        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """POST /powdercoat/jobs/add_item/ — { job_id, stock_item_id }"""
        job_id = request.data.get("job_id")
        stock_item_id = request.data.get("stock_item_id")
        from apps.inventory.models import StockItem

        job = PowdercoatJob.objects.get(id=job_id)
        si = StockItem.objects.get(id=stock_item_id)

        extr = si.product.extrusion.name if si.product.extrusion else si.product.code

        item = PowdercoatJobItem.objects.create(
            job=job,
            stock_item=si,
            extrusion=extr,
            style=getattr(si.product, "style", ""),
            length_mm=si.length_mm or 0,
            quantity=int(si.quantity),
            sent_state=si.state,
        )
        return Response(PowdercoatJobItemSerializer(item).data, status=201)


# ─────────────────────────────────────────────────────────────────────────────
# StockIssue ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class StockIssueViewSet(viewsets.ModelViewSet):
    queryset = StockIssue.objects.select_related("division", "receiving_location").all()
    serializer_class = StockIssueSerializer

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        """
        POST /stock-issues/{id}/issue/
        Issue stock from store to factory with outgoing QC check.
        """
        issue = self.get_object()
        if issue.status != "draft":
            return Response({"error": f"Cannot issue from status '{issue.status}'"}, status=400)

        with transaction.atomic():
            for line in issue.lines.select_related("stock_item").all():
                si = line.stock_item
                si.state = "stored"  # issued — in factory now
                si.save(update_fields=["state"])

            issue.status = "issued"
            issue.issued_date = request.data.get("issued_date")
            issue.issued_by = request.data.get("issued_by", "")
            issue.save(update_fields=["status", "issued_date", "issued_by"])

        return Response(StockIssueSerializer(issue).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        POST /stock-issues/{id}/confirm/
        Factory confirms receipt of issued stock.
        """
        issue = self.get_object()
        if issue.status != "issued":
            return Response({"error": f"Cannot confirm status '{issue.status}'"}, status=400)

        issue.status = "confirmed"
        issue.confirmed_date = request.data.get("confirmed_date")
        issue.received_by = request.data.get("received_by", "")
        issue.save(update_fields=["status", "confirmed_date", "received_by"])

        return Response(StockIssueSerializer(issue).data)