# manufacturing/views.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Job, ControlSheet, ControlSheetLine, CutRequirement, CutPlan
from .serializers import (
    JobSerializer, ControlSheetSerializer,
    ControlSheetLineSerializer, GenerateCutRequirementsSerializer,
)
from apps.cutting.models import CutDesign
from apps.cutting.views import _run_optimize


class IssueSheetPDFMixin:
    @action(detail=True, methods=["get"])
    def issue_sheet_pdf(self, request, pk=None):
        """GET /manufacturing/jobs/{id}/issue_sheet_pdf/ — Issue Sheet PDF."""
        job: Job = self.get_object()
        if not job.cut_design:
            return Response({"error": "No cut design linked. Run optimizer first."}, status=400)
        design = job.cut_design
        if design.status != "optimized":
            return Response({"error": "Cut design not yet optimized."}, status=400)

        import datetime
        year = datetime.date.today().year
        prefix = f"ISSUE-{year}-"
        from apps.powdercoat.models import StockIssue
        last = StockIssue.objects.filter(
            issue_number__startswith=prefix
        ).order_by("issue_number").last()
        seq = int(last.issue_number.split("-")[-1]) + 1 if last else 1
        issue_no = f"{prefix}{seq:04d}"

        from apps.reports.issue_sheet import generate_issue_sheet_pdf
        pdf_bytes = generate_issue_sheet_pdf(
            design,
            job_name=job.description or job.job_number,
            job_no=job.job_number,
            issue_no=issue_no,
            division_code=job.division.code,
        )
        from django.http import HttpResponse
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename={issue_no}.pdf"
        return response


class JobViewSet(IssueSheetPDFMixin, viewsets.ModelViewSet):
    queryset = Job.objects.select_related("division", "cut_design").all()
    serializer_class = JobSerializer

    @action(detail=True, methods=["post"])
    def generate_requirements(self, request, pk=None):
        """
        POST /manufacturing/jobs/{id}/generate_requirements/
        For each FINAL ControlSheet, create CutRequirements.
        Body: { "division_id": "uuid" }
        """
        job: Job = self.get_object()
        ser = GenerateCutRequirementsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        from apps.core.models import Division
        division = Division.objects.get(id=data["division_id"])

        final_sheets = job.control_sheets.filter(status="final")
        if not final_sheets.exists():
            return Response(
                {"error": "No final control sheets. Mark all sheets as 'final' first."},
                status=400,
            )

        job.cut_requirements.all().delete()
        created = 0
        for cs in final_sheets:
            for line in cs.lines.select_related("product").all():
                length = line.length_mm or (line.product.length_mm if line.product else None)
                if not length:
                    continue
                CutRequirement.objects.create(
                    job=job,
                    control_sheet=cs,
                    product=line.product,
                    cut_length_mm=length,
                    qty=line.quantity,
                    style=getattr(line.product, "style", ""),
                    colour=line.colour_name or getattr(line.product, "colour", ""),
                    colour_code=line.colour_code or getattr(line.product, "colour_code", ""),
                    allow_offcut_match=True,
                )
                created += 1

        job.status = "ready"
        job.save()

        return Response({
            "requirements_created": created,
            "message": f"Created {created} requirements. POST to run_optimizer next.",
        }, status=201)

    @action(detail=True, methods=["post"])
    def run_optimizer(self, request, pk=None):
        """POST /manufacturing/jobs/{id}/run_optimizer/"""
        job: Job = self.get_object()
        if not job.cut_requirements.exists():
            return Response({"error": "No cut requirements."}, status=400)

        cut_design, created = CutDesign.objects.get_or_create(
            job=job,
            defaults={
                "division": job.division,
                "name": f"{job.job_number} — Cut List",
                "offcut_keep_min_mm": 150,
                "status": "draft",
            }
        )
        if not created:
            cut_design.requirements.all().delete()
            cut_design.bars.all().delete()
            cut_design.offcuts.all().delete()

        for req in job.cut_requirements.select_related("product").all():
            cut_design.requirements.create(
                product=req.product,
                cut_length_mm=req.cut_length_mm,
                qty=req.qty,
                style=req.style,
                colour=req.colour,
                colour_code=req.colour_code,
            )

        result = _run_optimize(cut_design)
        if result.status_code == 200:
            job.cut_design = cut_design
            job.status = "cutting"
            job.save()
        return result

    @action(detail=True, methods=["post"])
    def mark_complete(self, request, pk=None):
        job: Job = self.get_object()
        job.status = "completed"
        job.save()
        return Response(JobSerializer(job).data)


class ControlSheetViewSet(viewsets.ModelViewSet):
    queryset = ControlSheet.objects.select_related("job").all()
    serializer_class = ControlSheetSerializer

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """POST /manufacturing/control-sheets/{id}/finalize/"""
        cs: ControlSheet = self.get_object()
        if cs.status == "issued":
            return Response({"error": "Already issued."}, status=400)
        cs.status = "final"
        cs.is_final = True
        cs.save()
        return Response(ControlSheetSerializer(cs).data)

    @action(detail=True, methods=["post"])
    def sign_off(self, request, pk=None):
        """POST /manufacturing/control-sheets/{id}/sign_off/"""
        from django.utils import timezone
        cs: ControlSheet = self.get_object()
        cs.status = "final"
        cs.is_final = True
        cs.signed_off_by = request.data.get("signed_off_by", "")
        cs.signed_off_at = timezone.now()
        cs.save()
        return Response(ControlSheetSerializer(cs).data)
