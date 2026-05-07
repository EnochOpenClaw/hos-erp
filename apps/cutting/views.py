# cutting/views.py
import math
import uuid
import logging
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Division, BinLocation
from apps.reports.cutting_diagram import generate_cutting_diagram_pdf
from .models import CutDesign, CutRequirement, CutBar, CutBarCut, Offcut, OffcutStatus
from .serializers import (
    CutDesignSerializer, CutDesignListSerializer,
    OptimizeRequestSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PuLP helpers (same logic as milp/solver_mixed_extrusion.py)
# ---------------------------------------------------------------------------

def _scale(val, scale=1000):
    return int(round(float(val) * scale))


def _unscale(val, scale=1000):
    return float(val) / scale


def _dedupe_preserve(vals):
    seen = set()
    out = []
    for x in vals:
        try:
            ix = int(round(float(x)))
        except Exception:
            continue
        if ix > 0 and ix not in seen:
            seen.add(ix)
            out.append(ix)
    return out


def _stock_opts(extrusion, cfg, stock_map):
    """Candidate stock lengths (mm) for an extrusion."""
    stock_cfg = (cfg.get("stock") or {}) if isinstance(cfg, dict) else {}
    base = (stock_cfg.get("default_stock_lengths") or {})
    if extrusion in base:
        opts = _as_list(base.get(extrusion))
    else:
        opts = []
    legacy = cfg.get("default_stock_lengths") or {}
    if extrusion in legacy:
        opts.extend(_as_list(legacy.get(extrusion)))
    if stock_map and extrusion in stock_map:
        opts.extend(_as_list(stock_map.get(extrusion)))
    out = _dedupe_preserve(opts)
    return out if out else [6300]


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


def _get_keep_min(cfg, extrusion):
    off = (cfg.get("offcuts") or {}) if isinstance(cfg, dict) else {}
    by_ex = off.get("offcut_keep_min_by_extrusion") or cfg.get("offcut_keep_min_by_extrusion") or {}
    base = off.get("offcut_keep_min_mm")
    if base is None:
        base = cfg.get("offcut_keep_min_mm", 150)
    try:
        base_i = int(float(base))
    except Exception:
        base_i = 150
    try:
        v = by_ex.get(extrusion)
        return int(float(v)) if v is not None else base_i
    except Exception:
        return base_i


def _flatten_demand(demand_by_item):
    """Flatten {item: {ex: {length: qty}}} → {ex: [(item, length, qty), ...]}."""
    cuts = defaultdict(list)
    for item, by_ex in (demand_by_item or {}).items():
        try:
            item_i = int(item)
        except Exception:
            try:
                item_i = int(float(item))
            except Exception:
                item_i = 1
        for ex, lens in (by_ex or {}).items():
            for L, q in (lens or {}).items():
                try:
                    qi = int(q)
                    Li = float(L)
                except Exception:
                    continue
                if qi > 0 and Li > 0:
                    cuts[ex].append((item_i, Li, qi))
    return dict(cuts)


def _build_item_pool(cut_list, scale=1000):
    pool = defaultdict(list)
    for item, L, q in cut_list:
        pool[_scale(L, scale)].extend([int(item)] * int(q))
    return pool


def _generate_patterns(lengths, stock_int, kerf_int, trim_int, max_patterns=6000):
    """FFD heuristic patterns."""
    capacity = stock_int - trim_int + kerf_int
    patterns = []
    seen = set()

    for start in lengths:
        cap = capacity
        pat = Counter()
        if start + kerf_int > cap:
            continue
        pat[start] += 1
        cap -= (start + kerf_int)
        for L in lengths:
            while L + kerf_int <= cap:
                pat[L] += 1
                cap -= (L + kerf_int)
        if sum(pat.values()) > 0:
            key = tuple(sorted(pat.items()))
            if key not in seen:
                seen.add(key)
                patterns.append(pat)

    # Pure patterns
    for L in lengths:
        maxc = capacity // (L + kerf_int)
        if maxc > 0:
            pat = Counter({L: int(maxc)})
            key = tuple(sorted(pat.items()))
            if key not in seen:
                seen.add(key)
                patterns.append(pat)

    return patterns[:max_patterns]


def _pattern_costs(pat, stock_int, kerf_int, trim_int, keep_min_int):
    n = int(sum(pat.values()))
    used = int(sum(L * c for L, c in pat.items()) + kerf_int * max(0, n - 1) + trim_int)
    waste = int(stock_int - used)
    if waste < 0:
        waste = 0
    if waste >= keep_min_int:
        return waste, 0, waste
    return waste, waste, 0


def _solve_extrusion_multi(cut_list, stock_opts_mm, cfg, timelimit=60):
    """Solve one extrusion type. Returns list of bar dicts."""
    scale = int(cfg.get("scale_factor", 1000))
    kerf = float(cfg.get("kerf_mm", 4.0))
    trim_start = float(cfg.get("trim_start_mm", 25.0))
    trim_end = float(cfg.get("trim_end_mm", 5.0))

    kerf_int = _scale(kerf, scale)
    trim_int = _scale(trim_start + trim_end, scale)

    demand_int = Counter()
    pool_items = defaultdict(list)
    for item, L, q in cut_list:
        Li = float(L)
        Ls = _scale(Li, scale)
        demand_int[Ls] += int(q)
        pool_items[Ls].extend([int(item)] * int(q))

    lengths = sorted(demand_int.keys(), reverse=True)
    if not lengths:
        return []

    keep_min_mm = cfg.get("_keep_min_mm_for_current_extrusion", 150)
    keep_min_int = _scale(keep_min_mm, scale)

    pattern_bank = []
    for stock_mm in stock_opts_mm:
        stock_int = _scale(stock_mm, scale)
        pats = _generate_patterns(lengths, stock_int, kerf_int, trim_int)
        for pat in pats:
            waste, discard, keepable = _pattern_costs(pat, stock_int, kerf_int, trim_int, keep_min_int)
            if sum(pat.values()) <= 0:
                continue
            pattern_bank.append({
                "stock_mm": float(stock_mm),
                "pat": pat,
                "waste": waste,
                "discard": discard,
                "keepable": keepable,
            })

    if not pattern_bank:
        # Fallback: naive one-cut-per-bar
        bars = []
        stock_mm = float(max(stock_opts_mm) if stock_opts_mm else 6300)
        for Ls in lengths:
            for _ in range(demand_int[Ls]):
                item = pool_items[Ls].pop() if pool_items[Ls] else 1
                bars.append({
                    "bar_no": len(bars) + 1,
                    "stock_len": stock_mm,
                    "cuts": [{"item": item, "length_mm": _unscale(Ls, scale)}],
                    "offcut_mm": round(stock_mm - _unscale(Ls, scale), 3),
                })
        return bars

    # ---- MILP via PuLP ----
    try:
        import pulp
        HAVE_PULP = True
    except Exception:
        HAVE_PULP = False

    if not HAVE_PULP:
        # Greedy fallback
        stock_mm = float(max(stock_opts_mm) if stock_opts_mm else 6300)
        items = []
        for item, L, q in cut_list:
            items.extend([{"item": int(item), "length_mm": float(L)}] * int(q))
        items.sort(key=lambda d: -d["length_mm"])
        bars = []
        for it in items:
            placed = False
            for b in bars:
                n = len(b["cuts"])
                used = sum(c["length_mm"] for c in b["cuts"]) + kerf * max(0, n - 1) + (trim_start + trim_end)
                if used + it["length_mm"] + (kerf if n > 0 else 0) <= stock_mm + 1e-6:
                    b["cuts"].append(it)
                    placed = True
                    break
            if not placed:
                bars.append({"bar_no": len(bars) + 1, "stock_len": stock_mm, "cuts": [it]})
        for b in bars:
            n = len(b["cuts"])
            used = sum(c["length_mm"] for c in b["cuts"]) + kerf * max(0, n - 1) + (trim_start + trim_end)
            b["offcut_mm"] = round(stock_mm - used, 3)
        return bars

    P = len(pattern_bank)
    counts = [[int(p["pat"].get(L, 0)) for L in lengths] for p in pattern_bank]
    discards = [int(p["discard"]) for p in pattern_bank]
    keepables = [int(p["keepable"]) for p in pattern_bank]

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=timelimit)

    # Stage 1: minimize discard
    prob1 = pulp.LpProblem("MinDiscard", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", lowBound=0, cat=pulp.LpInteger) for i in range(P)]
    for j, L in enumerate(lengths):
        prob1 += pulp.lpSum(counts[i][j] * x[i] for i in range(P)) == demand_int[L]
    discard_expr = pulp.lpSum(discards[i] * x[i] for i in range(P))
    prob1 += discard_expr
    prob1.solve(solver)
    best_discard = int(round(pulp.value(discard_expr) or 0))

    # Stage 2: maximize keepable (min negative keepable)
    prob2 = pulp.LpProblem("MaxKeepable", pulp.LpMinimize)
    y = [pulp.LpVariable(f"y_{i}", lowBound=0, cat=pulp.LpInteger) for i in range(P)]
    for j, L in enumerate(lengths):
        prob2 += pulp.lpSum(counts[i][j] * y[i] for i in range(P)) == demand_int[L]
    keep_expr2 = pulp.lpSum(keepables[i] * y[i] for i in range(P))
    prob2 += pulp.lpSum(discards[i] * y[i] for i in range(P)) == best_discard
    prob2 += -keep_expr2
    prob2.solve(solver)
    best_keep = int(round(pulp.value(keep_expr2) or 0))

    # Stage 3: minimize bars tie-break
    prob3 = pulp.LpProblem("MinBars", pulp.LpMinimize)
    z = [pulp.LpVariable(f"z_{i}", lowBound=0, cat=pulp.LpInteger) for i in range(P)]
    for j, L in enumerate(lengths):
        prob3 += pulp.lpSum(counts[i][j] * z[i] for i in range(P)) == demand_int[L]
    prob3 += pulp.lpSum(discards[i] * z[i] for i in range(P)) == best_discard
    prob3 += pulp.lpSum(keepables[i] * z[i] for i in range(P)) == best_keep
    prob3 += pulp.lpSum(z)
    prob3.solve(solver)
    sol_mult = [int(round(v.value() or 0)) for v in z]

    # Build bars
    bars = []
    for i, mult in enumerate(sol_mult):
        if mult <= 0:
            continue
        p = pattern_bank[i]
        pat = p["pat"]
        stock_mm = float(p["stock_mm"])
        for _k in range(mult):
            cuts_out = []
            for Ls, c in pat.items():
                for _j in range(int(c)):
                    item = pool_items[Ls].pop() if pool_items[Ls] else 1
                    cuts_out.append({"item": int(item), "length_mm": _unscale(Ls, scale)})
            cuts_out.sort(key=lambda d: (-float(d["length_mm"]), int(d["item"])))
            n = len(cuts_out)
            used = sum(c["length_mm"] for c in cuts_out) + kerf * max(0, n - 1) + (trim_start + trim_end)
            offcut = round(stock_mm - used, 3)
            bars.append({
                "bar_no": len(bars) + 1,
                "stock_len": stock_mm,
                "cuts": cuts_out,
                "offcut_mm": offcut,
            })

    return bars


def _solve_bar_plan(demand_by_item, stock_map, cfg, timelimit=60):
    """Solve all extrusion types. Returns {ex: [bars...]."""
    cuts_by_ex = _flatten_demand(demand_by_item)
    bar_plan = {}
    for ex, cut_list in cuts_by_ex.items():
        stock_opts = _stock_opts(ex, cfg, stock_map)
        keep_min = _get_keep_min(cfg, ex)
        cfg2 = dict(cfg or {})
        cfg2["_keep_min_mm_for_current_extrusion"] = keep_min
        bars = _solve_extrusion_multi(cut_list, stock_opts, cfg2, timelimit=timelimit)
        bar_plan[ex] = bars
    return bar_plan


# ---------------------------------------------------------------------------
# Offcut matching helpers
# ---------------------------------------------------------------------------

def _match_offcut_for_requirement(offcut_qs, req, keep_min_mm):
    """
    Find the best reusable offcut for a CutRequirement.
    Returns (offcut, remaining_mm) or (None, None).
    """
    for offcut in offcut_qs.filter(status=OffcutStatus.IN_STOCK).order_by("-length_mm"):
        if not offcut.can_consume_for(req, keep_min_mm):
            continue
        return offcut, float(offcut.length_mm) - float(req.cut_length_mm)
    return None, None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class CutDesignViewSet(viewsets.ModelViewSet):
    queryset = CutDesign.objects.all()
    serializer_class = CutDesignSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CutDesignListSerializer
        return CutDesignSerializer

    @action(detail=True, methods=["post"])
    def optimize(self, request, pk=None):
        """
        POST /cutting/designs/{id}/optimize/

        Runs the MILP cut optimizer for this CutDesign's requirements.
        Creates CutBar, CutBarCut, and Offcut records.
        One pass only — re-running replaces all bars/offcuts.
        """
        design: CutDesign = self.get_object()
        return _run_optimize(design)

    @action(detail=False, methods=["post"])
    def quick_optimize(self, request):
        """
        POST /cutting/designs/quick_optimize/

        Body (JSON):
        {
            "division_id": "uuid",
            "requirements": [
                {"product_id": "uuid", "cut_length_mm": 2663, "qty": 4, "style": "", "colour": "", "colour_code": ""},
                ...
            ],
            "offcut_keep_min_mm": 150,
            "config": {}   // optional overrides
        }
        Creates a CutDesign + CutRequirements, runs optimizer, returns design.
        """
        ser = OptimizeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        division = Division.objects.get(id=data["division_id"])
        design = CutDesign.objects.create(
            division=division,
            name=data.get("name", ""),
            job_no=data.get("job_no", ""),
            offcut_keep_min_mm=data.get("offcut_keep_min_mm", 150),
            config_json=data.get("config", {}),
            status="draft",
        )

        for req_data in data.get("requirements", []):
            CutRequirement.objects.create(
                design=design,
                product_id=req_data["product_id"],
                cut_length_mm=req_data["cut_length_mm"],
                qty=req_data["qty"],
                style=req_data.get("style", ""),
                colour=req_data.get("colour", ""),
                colour_code=req_data.get("colour_code", ""),
            )

        return _run_optimize(design)

    @action(detail=True, methods=["get"])
    def cutting_diagram_pdf(self, request, pk=None):
        """
        GET /cutting/designs/{id}/cutting_diagram_pdf/
        Returns the cutting diagram as a PDF.
        """
        design: CutDesign = self.get_object()
        if design.status != "optimized" or not design.bar_plan_json:
            return Response(
                {"error": "Design has not been optimized yet. "
                          "POST /designs/{id}/optimize/ first."},
                status=400,
            )
        pdf_bytes = generate_cutting_diagram_pdf(design)
        from django.http import HttpResponse
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"CuttingDiagram_{design.job_no or design.id}.pdf"
        response["Content-Disposition"] = f"inline; filename={filename}"
        return response


def _run_optimize(design: CutDesign) -> Response:
    """
    Core optimize logic:
    1. Load requirements → build demand dict
    2. Try to match reusable offcuts from inventory
    3. Run MILP solver (one pass)
    4. Save CutBar + CutBarCut + Offcut records
    5. Mark matched offcuts as reserved
    """
    requirements = list(design.requirements.select_related("product").all())
    if not requirements:
        return Response({"error": "No requirements on this design"}, status=400)

    keep_min = design.offcut_keep_min_mm
    cfg = dict(design.config_json or {})
    cfg["offcut_keep_min_mm"] = keep_min
    # Default cutting params if not in config
    cfg.setdefault("kerf_mm", 4.0)
    cfg.setdefault("trim_start_mm", 25.0)
    cfg.setdefault("trim_end_mm", 5.0)
    cfg.setdefault("scale_factor", 1000)

    # --- Step 1: build demand by item+extrusion ---
    # Group requirements by their extrusion identity
    # Key: (extrusion_lower, style_lower, colour_lower, colour_code_lower)
    demand_raw = defaultdict(lambda: defaultdict(Counter))
    req_by_key = {}

    for req in requirements:
        extr = (req.product.extrusion.name if req.product.extrusion else "").strip()
        style = (req.style or "").strip()
        colour = (req.colour or "").strip()
        code = (req.colour_code or "").strip()
        key = (extr.lower(), style.lower(), colour.lower(), code.lower())

        demand_raw[key][extr][float(req.cut_length_mm)] += int(req.qty)
        req_by_key[key] = req

    # Reorganize: demand_by_item = { item_id: { ex: { length: qty } } }
    demand_by_item = {}
    for idx, (key, ex_dict) in enumerate(demand_raw.items()):
        item_id = idx + 1
        demand_by_item[str(item_id)] = dict(ex_dict)

    # --- Step 2: try offcut reuse ---
    # Build per-(extrusion, style, colour, code) offcut queryset lookup
    offcut_qs = Offcut.objects.filter(status=OffcutStatus.IN_STOCK)
    used_offcut_ids = set()

    # Substitution map: for each requirement key, how many offcuts to try to use
    # We'll track consumed offcuts per requirement
    req_offcut_map = {}  # req_key -> list of (offcut, remaining_mm)

    for req in requirements:
        extr = (req.product.extrusion.name if req.product.extrusion else "").strip()
        style = (req.style or "").strip()
        colour = (req.colour or "").strip()
        code = (req.colour_code or "").strip()

        # Filter by extrusion + style compatibility
        candidates = offcut_qs.filter(
            extrusion__iexact=extr,
        )
        matched = []
        for off in candidates.order_by("-length_mm"):
            if off.id in used_offcut_ids:
                continue
            if not off.can_consume_for(req, keep_min):
                continue
            used_offcut_ids.add(off.id)
            remaining = float(off.length_mm) - float(req.cut_length_mm)
            matched.append((off, remaining))

        req_offcut_map[req.id] = matched

    # --- Step 3: build demand with offcut reuse accounted for ---
    # For each req, reduce demand by number of matched offcuts
    req_demand = {req.id: int(req.qty) for req in requirements}
    offcut_bar_source = {}  # offcut.id -> bar_dict being built

    for req in requirements:
        matched = req_offcut_map.get(req.id, [])
        for off, remaining in matched:
            req_demand[req.id] -= 1

    # Build final demand dict for solver
    final_demand = {}
    for idx, req in enumerate(requirements):
        item_id = idx + 1
        extr = (req.product.extrusion.name if req.product.extrusion else "").strip()
        L = float(req.cut_length_mm)
        q = req_demand[req.id]
        if q > 0:
            if str(item_id) not in final_demand:
                final_demand[str(item_id)] = {}
            if extr not in final_demand[str(item_id)]:
                final_demand[str(item_id)][extr] = {}
            final_demand[str(item_id)][extr][L] = q

    # --- Step 4: solve ---
    bar_plan = _solve_bar_plan(final_demand, {}, cfg, timelimit=60)

    # --- Step 5: persist ---
    with transaction.atomic():
        # Wipe existing bars/offcuts for this design (re-run protection)
        design.bars.all().delete()
        design.offcuts.all().delete()
        # Reset allocated_qty on requirements
        design.requirements.all().update(allocated_qty=0)

        bar_counter = 0

        for ex, bars in bar_plan.items():
            for bar_data in bars:
                bar_counter += 1
                bar = CutBar.objects.create(
                    design=design,
                    bar_no=bar_counter,
                    stock_len_mm=bar_data["stock_len"],
                    kerf_mm=cfg.get("kerf_mm", 4.0),
                    trim_start_mm=cfg.get("trim_start_mm", 25.0),
                    trim_end_mm=cfg.get("trim_end_mm", 5.0),
                    offcut_mm=bar_data["offcut_mm"],
                    group_key=ex,
                )

                # Create cut lines
                pos = float(cfg.get("trim_start_mm", 25.0))
                for cut_info in bar_data["cuts"]:
                    item_id = cut_info["item"]
                    length = cut_info["length_mm"]
                    # Find which requirement this item belongs to
                    # We track by item index in final_demand
                    req = None
                    for idx2, req2 in enumerate(requirements):
                        if idx2 + 1 == item_id:
                            req = req2
                            break
                    CutBarCut.objects.create(
                        bar=bar,
                        requirement=req,
                        position_mm=pos,
                        length_mm=length,
                        item_id=item_id,
                    )
                    pos += length + float(cfg.get("kerf_mm", 4.0))
                    if req:
                        req.allocated_qty += 1
                        req.save(update_fields=["allocated_qty"])

                # Create Offcut record for keepable offcuts
                if bar_data["offcut_mm"] >= keep_min:
                    # Get style/colour/code from the bar's cuts' requirements
                    bar_reqs = bar.cut_lines.exclude(requirement__isnull=True).select_related("requirement__product__extrusion")
                    first_req = bar_reqs.first()
                    if first_req and first_req.requirement:
                        r = first_req.requirement
                        extr_name = r.product.extrusion.name if r.product.extrusion else ex
                        style = r.style or ""
                        colour = r.colour or ""
                        colour_code = r.colour_code or ""
                    else:
                        extr_name = ex
                        style = ""
                        colour = ""
                        colour_code = ""

                    # Find a suitable bin
                    bin_loc = None
                    try:
                        offcut_storage = BinLocation.objects.filter(
                            location__type__iexact="offcut_storage",
                            location__division=design.division,
                        ).first()
                        bin_loc = offcut_storage
                    except Exception:
                        pass

                    Offcut.objects.create(
                        design=design,
                        bar=bar,
                        source_job_name=design.name or "",
                        source_job_no=design.job_no or "",
                        extrusion=extr_name,
                        style=style,
                        colour=colour,
                        colour_code=colour_code,
                        length_mm=bar_data["offcut_mm"],
                        stock_len_mm=bar_data["stock_len"],
                        bin_location=bin_loc,
                        status=OffcutStatus.IN_STOCK,
                    )

        # Mark matched offcuts as reserved
        reserved = Offcut.objects.filter(id__in=used_offcut_ids)
        reserved.update(status=OffcutStatus.RESERVED)

        design.bar_plan = bar_plan
        design.status = "optimized"
        design.save()

    serializer = CutDesignSerializer(design)
    return Response(serializer.data, status=200)
