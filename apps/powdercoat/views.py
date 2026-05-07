# powdercoat/views.py
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    QualityCheck, PowdercoatSupplier, PowdercoatJob,
    PowdercoatJobItem, StockIssue, StockIssueLine,
)
from .serializers import (
    QualityCheckSerializer, PowdercoatJobSerializer,
    StockIssueSerializer, CreateQCCheckSerializer,
)


class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.all()
    serializer_class = QualityCheckSerializer


class PowdercoatSupplierViewSet(viewsets.ModelViewSet):
    queryset = PowdercoatSupplier.objects.all()


class PowdercoatJobViewSet(viewsets.ModelViewSet):
    queryset = PowdercoatJob.objects.all()
    serializer_class = PowdercoatJobSerializer

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/send/
        Mark job as sent. QC check included in body.
        """
        job = self.get_object()
        ser = CreateQCCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        with transaction.atomic():
            # Outgoing QC check
            qc = QualityCheck.objects.create(
                check_type="outgoing_powder",
                result=data["result"],
                powdercoat_job=job,
                checked_by=data.get("checked_by", ""),
                notes=data.get("notes", ""),
                fail_reason=data.get("fail_reason", ""),
                condition=data.get("condition", ""),
            )

            if data["result"] == "fail":
                return Response({"error": "Cannot send — QC failed", "qc": QualityCheckSerializer(qc).data}, status=400)

            # Update job state
            job.status = "sent"
            job.sent_date = job.sent_date or timezone.now().date()
            job.save()

            # Update each StockItem
            for item in job.items.select_related("stock_item"):
                if item.stock_item.state not in ("stored", "issued"):
                    continue
                item.sent_state = item.stock_item.state
                item.save()
                item.stock_item.state = "sent_powder"
                item.stock_item.save(update_fields=["state"])

        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/receive/
        Record return from powder coater with QC check.
        """
        job = self.get_object()
        ser = CreateQCCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if job.status == "completed":
            return Response({"error": "Job already completed"}, status=400)

        with transaction.atomic():
            # Incoming QC
            qc = QualityCheck.objects.create(
                check_type="incoming_powder",
                result=data["result"],
                powdercoat_job=job,
                checked_by=data.get("checked_by", ""),
                notes=data.get("notes", ""),
                fail_reason=data.get("fail_reason", ""),
                condition=data.get("condition", ""),
            )

            job.status = "returned"
            job.returned_date = job.returned_date or timezone.now().date()
            job.save()

            for item in job.items.select_related("stock_item"):
                item.returned_state = item.stock_item.state
                item.save()
                item.stock_item.state = "returned_powder"
                item.stock_item.powder_color = job.powder_color
                item.stock_item.save(update_fields=["state", "powder_color"])

        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        POST /powdercoat/jobs/{id}/complete/
        Mark all items fully received and job completed.
        """
        job = self.get_object()
        job.status = "completed"
        job.save()
        return Response(PowdercoatJobSerializer(job).data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """
        POST /powdercoat/jobs/add_item/
        Body: { job_id, stock_item_id }
        Add a StockItem to a PowdercoatJob.
        """
        job_id = request.data.get("job_id")
        stock_item_id = request.data.get("stock_item_id")
        from apps.inventory.models import StockItem

        job = PowdercoatJob.objects.get(id=job_id)
        si = StockItem.objects.get(id=stock_item_id)

        if si.product.extrusion:
            extr = si.product.extrusion.name
        else:
            extr = si.product.code

        item = PowdercoatJobItem.objects.create(
            job=job,
            stock_item=si,
            extrusion=extr,
            style=getattr(si.product, "style", ""),
            length_mm=si.length_mm or 0,
            quantity=int(si.quantity),
            sent_state=si.state,
        )
        from .serializers import PowdercoatJobItemSerializer
        return Response(PowdercoatJobItemSerializer(item).data, status=201)


class StockIssueViewSet(viewsets.ModelViewSet):
    queryset = StockIssue.objects.all()
    serializer_class = StockIssueSerializer

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        """
        POST /stock-issues/{id}/issue/
        Issue stock to factory with QC check.
        """
        issue = self.get_object()
        ser = CreateQCCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        with transaction.atomic():
            # Issue QC check
            qc = QualityCheck.objects.create(
                check_type="issue_factory",
                result=data["result"],
                checked_by=data.get("checked_by", ""),
                notes=data.get("notes", ""),
                fail_reason=data.get("fail_reason", ""),
                condition=data.get("condition", ""),
            )

            if data["result"] == "fail":
                return Response({"error": "Cannot issue — QC failed"}, status=400)

            issue.status = "issued"
            issue.issued_date = issue.issued_date or timezone.now().date()
            issue.save()

            for line in issue.lines.select_related("stock_item"):
                line.stock_item.state = "issued"
                line.stock_item.bin_location = None
                line.stock_item.save(update_fields=["state", "bin_location"])

        return Response(StockIssueSerializer(issue).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        POST /stock-issues/{id}/confirm/
        Factory confirms receipt of issued stock.
        """
        issue = self.get_object()
        if issue.status != "issued":
            return Response({"error": "Must be issued first"}, status=400)

        received_by = request.data.get("received_by", "")
        notes = request.data.get("notes", "")

        issue.status = "confirmed"
        issue.confirmed_date = timezone.now().date()
        issue.received_by = received_by
        issue.notes = (issue.notes or "") + (" | Confirmed: " + notes if notes else "")
        issue.save()
        return Response(StockIssueSerializer(issue).data)
