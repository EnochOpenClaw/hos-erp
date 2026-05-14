# manufacturing/views.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Company
from .models import Job, ControlSheet, ControlSheetLine, CutRequirement, CutPlan
from .serializers import (
    JobSerializer, JobListSerializer,
    ControlSheetSerializer, ControlSheetLineSerializer,
    CutRequirementSerializer,
    GenerateCutRequirementsSerializer,
)
from apps.cutting.models import CutDesign, CutBar, CutBarCut
from apps.cutting.views import _run_optimize


# ─────────────────────────────────────────────────────────────────────────────
# Issue Sheet PDF mixin
# ─────────────────────────────────────────────────────────────────────────────

class IssueSheetPDFMixin:
    @action(detail=True, methods=["get"])
    def issue_sheet_pdf(self, request, pk=None):
        """GET /manufacturing/jobs/{id}/issue_sheet_pdf/ — Issue Sheet PDF."""
        job = self.get_object()
        if not job.cut_design:
            return Response({"error": "No cut design linked. Run optimizer first."}, status=400)
        design = job.cut_design
        if design.status != "optimized":
            return Response({"error": "Cut design not yet optimized."}, status=400)

        year = timezone.now().year
        prefix = f"ISSUE-{year}-"
        last = StockIssue.objects.filter(issue_number__startswith=prefix).order_by("issue_number").last() if hasattr(__import__('apps.powdercoat', fromlist=['models']), 'StockIssue') else None
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


# ─────────────────────────────────────────────────────────────────────────────
# Job ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class JobViewSet(IssueSheetPDFMixin, viewsets.ModelViewSet):
    queryset = Job.objects.select_related("division", "cut_design").all()

    def get_serializer_class(self):
        if self.action == "list":
            return JobListSerializer
        return JobSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["company"] = Company.objects.filter(name="OpenFactory Systems").first()
        return ctx

    def get_queryset(self):
        qs = Job.objects.filter(company__name="OpenFactory Systems").select_related("division", "cut_design")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(job_number__icontains=search, customer_name__icontains=search)
        st = self.request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        div = self.request.query_params.get("division")
        if div:
            qs = qs.filter(division_id=div)
        return qs

    @action(detail=True, methods=["post"])
    def generate_requirements(self, request, pk=None):
        """POST /manufacturing/jobs/{id}/generate_requirements/"""
        job = self.get_object()
        ser = GenerateCutRequirementsSerializer(data=request.data, context={"job": job})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        final_sheets = job.control_sheets.filter(status="final")
        if not final_sheets.exists():
            return Response({"error": "No final control sheets."}, status=400)

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
                    style=line.product.style or "",
                    colour=cs.colour_name or line.product.colour or "",
                    colour_code=cs.colour_code or line.product.colour_code or "",
                    allow_offcut_match=True,
                )
                created += 1

        job.status = "ready"
        job.save()
        return Response({"requirements_created": created}, status=201)

    @action(detail=True, methods=["post"])
    def run_optimizer(self, request, pk=None):
        """POST /manufacturing/jobs/{id}/run_optimizer/"""
        job = self.get_object()
        if not job.cut_requirements.exists():
            return Response({"error": "No cut requirements."}, status=400)

        cut_design = CutDesign.objects.filter(manufacturing_jobs__id=job.id).first()
        if not cut_design:
            cut_design = CutDesign.objects.create(
                division=job.division,
                name=f"{job.job_number} — Cut List",
                offcut_keep_min_mm=150,
                status="draft",
            )
            # Wire the FK from Job side
            job.cut_design = cut_design
            job.save(update_fields=["cut_design"])

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
        job = self.get_object()
        job.status = "completed"
        job.save()
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def add_control_sheet(self, request, pk=None):
        """POST /manufacturing/jobs/{id}/add_control_sheet/ — create a new blank sheet."""
        job = self.get_object()
        next_num = job.control_sheets.count() + 1
        cs = ControlSheet.objects.create(
            job=job,
            sheet_number=next_num,
            name=request.data.get("name", f"Opening {next_num}"),
            opening_type=request.data.get("opening_type", "door"),
            status="draft",
        )
        return Response(ControlSheetSerializer(cs).data)

    @action(detail=True, methods=["post"])
    def add_cut_requirement(self, request, pk=None):
        """POST /manufacturing/jobs/{id}/add_cut_requirement/ — add a line to a job."""
        job = self.get_object()
        req = CutRequirement.objects.create(
            job=job,
            product_id=request.data["product_id"],
            cut_length_mm=request.data["cut_length_mm"],
            qty=request.data.get("qty", 1),
        )
        return Response(CutRequirementSerializer(req).data)


# ─────────────────────────────────────────────────────────────────────────────
# ControlSheet ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class ControlSheetViewSet(viewsets.ModelViewSet):
    queryset = ControlSheet.objects.select_related("job").all()
    serializer_class = ControlSheetSerializer

    def get_queryset(self):
        qs = ControlSheet.objects.filter(job__company__name="OpenFactory Systems")
        job_id = self.request.query_params.get("job")
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["company"] = Company.objects.filter(name="OpenFactory Systems").first()
        return ctx

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        cs = self.get_object()
        if cs.status == "issued":
            return Response({"error": "Already issued."}, status=400)
        cs.status = "final"
        cs.is_final = True
        cs.save()
        return Response(ControlSheetSerializer(cs).data)

    @action(detail=True, methods=["post"])
    def sign_off(self, request, pk=None):
        cs = self.get_object()
        cs.status = "final"
        cs.is_final = True
        cs.signed_off_by = request.data.get("signed_off_by", "")
        cs.signed_off_at = timezone.now()
        cs.save()
        return Response(ControlSheetSerializer(cs).data)


# ─────────────────────────────────────────────────────────────────────────────
# ControlSheetLine ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class ControlSheetLineViewSet(viewsets.ModelViewSet):
    queryset = ControlSheetLine.objects.select_related("product", "control_sheet").all()
    serializer_class = ControlSheetLineSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["company"] = Company.objects.filter(name="OpenFactory Systems").first()
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# CutRequirement ViewSet
# ─────────────────────────────────────────────────────────────────────────────

class CutRequirementViewSet(viewsets.ModelViewSet):
    queryset = CutRequirement.objects.select_related("product", "job").all()
    serializer_class = CutRequirementSerializer

    def get_queryset(self):
        qs = CutRequirement.objects.filter(job__company__name="OpenFactory Systems")
        job_id = self.request.query_params.get("job")
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# Factory Floor Cutting Queue
# ─────────────────────────────────────────────────────────────────────────────

class CuttingQueueViewSet(viewsets.ViewSet):
    """
    GET  /manufacturing/factory/queue/                        — job list (FIFO)
    POST /manufacturing/factory/queue/reorder/                 — { job_ids: [...] }
    GET  /manufacturing/factory/queue/{job_id}/               — per-job detail
    POST /manufacturing/factory/queue/{job_id}/flip_bar/{bar_id}/   — flip onto machine
    POST /manufacturing/factory/queue/{job_id}/mark_cut/{cut_id}/   — toggle cut done
    POST /manufacturing/factory/queue/{job_id}/reset_bar/{bar_id}/  — reset bar
    """

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """POST /manufacturing/factory/queue/reorder/ — { job_ids: [...] } sets priority."""
        ids = request.data.get("job_ids", [])
        if not isinstance(ids, list):
            return Response({"error": "job_ids must be a list"}, status=400)
        for idx, job_id in enumerate(ids):
            Job.objects.filter(id=job_id).update(priority=idx)
        return Response({"updated": len(ids)})

    def list(self, request):
        """All jobs in cutting queue, ordered by priority then created_at."""
        jobs = Job.objects.filter(
            status__in=["ready", "cutting"]
        ).select_related("division", "cut_design").order_by("priority", "created_at")

        data = []
        for job in jobs:
            cd = job.cut_design
            if not cd:
                continue
            bars = list(cd.bars.all())
            if not bars:
                continue
            total_cuts = sum(b.cut_lines.count() for b in bars)
            done_cuts  = sum(b.cut_lines.filter(is_cut=True).count() for b in bars)
            done_bars  = sum(1 for b in bars if b.is_complete)
            data.append({
                "job_id":        str(job.id),
                "job_number":   job.job_number,
                "description":   job.description or "",
                "division":      job.division.code,
                "priority":      getattr(job, "priority", 0),
                "total_bars":    len(bars),
                "done_bars":     done_bars,
                "total_cuts":    total_cuts,
                "done_cuts":     done_cuts,
                "progress_pct":  round(done_cuts / total_cuts * 100, 1) if total_cuts else 0,
                "status":        job.status,
            })
        return Response(data)

    def retrieve(self, request, pk=None):
        """
        Per-job cutting screen.
        Returns keepable offcuts first, then bars grouped by extrusion section.
        """
        job = get_object_or_404(Job, id=pk)
        cd = job.cut_design
        if not cd:
            return Response({"error": "No cut design linked."}, status=404)

        keepable = list(cd.offcuts.filter(status="in_stock").select_related("bin_location").order_by("length_mm"))

        bars_qs = cd.bars.order_by("bar_no")
        sections = {}
        for bar in bars_qs:
            key = bar.group_key or "Other"
            parts = [p.strip() for p in key.split("|")]
            extr  = parts[0] if len(parts) > 0 else "Other"
            colour = parts[1] if len(parts) > 1 else ""
            code   = parts[2] if len(parts) > 2 else ""
            stock  = parts[3] if len(parts) > 3 else ""

            if key not in sections:
                sections[key] = {
                    "heading":     f"{extr} – {colour} – {code}" + (f" — {stock}" if stock else ""),
                    "extrusion":   extr,
                    "colour":      colour,
                    "colour_code": code,
                    "stock_len":   stock,
                    "bars": [],
                }

            cuts = bar.cut_lines.select_related("requirement").order_by("position_mm")
            cut_data = []
            for c in cuts:
                req = c.requirement
                cut_data.append({
                    "cut_id":      str(c.id),
                    "bar_id":      str(bar.id),
                    "position_mm": float(c.position_mm),
                    "length_mm":   float(c.length_mm),
                    "item_id":     c.item_id,
                    "is_cut":      c.is_cut,
                    "style":       req.style if req else "",
                    "colour":      req.colour if req else colour,
                    "colour_code": req.colour_code if req else code,
                })

            is_keep = float(bar.offcut_mm) >= cd.offcut_keep_min_mm
            offcut_bin = ""
            if is_keep:
                off = next((o for o in keepable if str(o.bar_id) == str(bar.id)), None)
                if off and off.bin_location:
                    offcut_bin = off.bin_location.code

            sections[key]["bars"].append({
                "bar_id":      str(bar.id),
                "bar_no":      bar.bar_no,
                "stock_len":   float(bar.stock_len_mm),
                "offcut_mm":   float(bar.offcut_mm),
                "offcut_keep": is_keep,
                "offcut_bin":  offcut_bin,
                "is_flipped":  bar.is_flipped,
                "is_complete": bar.is_complete,
                "cuts":        cut_data,
            })

        offcut_list = [{
            "id":          str(o.id),
            "extrusion":   o.extrusion,
            "style":       o.style,
            "colour":      o.colour,
            "colour_code": o.colour_code,
            "length_mm":   float(o.length_mm),
            "bin_code":    o.bin_location.code if o.bin_location else "UNASSIGNED",
            "stock_len":   float(o.stock_len_mm) if o.stock_len_mm else 0,
        } for o in keepable]

        return Response({
            "job_id":             str(job.id),
            "job_number":        job.job_number,
            "description":       job.description or "",
            "division":          job.division.code,
            "status":            job.status,
            "offcut_keep_min_mm": cd.offcut_keep_min_mm,
            "offcuts":           offcut_list,
            "sections":          list(sections.values()),
        })

    @action(detail=True, methods=["post"], url_path="flip_bar(?P<bar_id>[^/.]+)")
    def flip_bar(self, request, pk=None, bar_id=None):
        bar = get_object_or_404(CutBar, id=bar_id, design__manufacturing_jobs__id=pk)
        bar.is_flipped = not bar.is_flipped
        bar.save(update_fields=["is_flipped"])
        return Response({"bar_id": str(bar.id), "is_flipped": bar.is_flipped})

    @action(detail=True, methods=["post"], url_path="mark_cut(?P<cut_id>[^/.]+)")
    def mark_cut(self, request, pk=None, cut_id=None):
        cut = get_object_or_404(CutBarCut, id=cut_id, bar__design__manufacturing_jobs__id=pk)
        cut.is_cut = not cut.is_cut
        cut.save(update_fields=["is_cut"])

        bar = cut.bar
        if bar.is_complete and not bar.is_flipped:
            bar.is_flipped = True
            bar.save(update_fields=["is_flipped"])

        return Response({
            "cut_id":       str(cut.id),
            "is_cut":       cut.is_cut,
            "bar_complete": bar.is_complete,
            "bar_flipped":  bar.is_flipped,
        })

    @action(detail=True, methods=["post"], url_path="reset_bar(?P<bar_id>[^/.]+)")
    def reset_bar(self, request, pk=None, bar_id=None):
        bar = get_object_or_404(CutBar, id=bar_id, design__manufacturing_jobs__id=pk)
        bar.is_flipped = False
        bar.save(update_fields=["is_flipped"])
        bar.cut_lines.all().update(is_cut=False)
        return Response({"bar_id": str(bar.id), "is_flipped": False, "cuts_reset": bar.cut_lines.count()})