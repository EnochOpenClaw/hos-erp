# reports/cutting_diagram.py
"""
Cutting Diagram PDF Renderer — matches the physical sample format.

Header every page:  "CUTTING DIAGRAMS (Operator) — Mixed Items" | "Job: {name}  Job No: {no}"
Footer every page:  "Page X of Y" (right)

Each section:
  Heading: "{Extrusion} – {Colour} – {ColourCode} - {StockLen}"
  Then per bar: "Bar #{no}" | coloured chips (item · length) | Offcut (green/red)
  Overflow → "Bar #{no} (cont.)" continuation rows
  Offcut badge appears only on the LAST row of a bar
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT


# ── Colour palette: one colour per item number ─────────────────────────────────
ITEM_COLOURS = [
    "#2563EB", "#DC2626", "#16A34A", "#D97706", "#7C3AED",
    "#0891B2", "#DB2777", "#EA580C", "#4F46E5", "#65A30D",
    "#0284C7", "#BE123C", "#047857", "#9333EA", "#C2410C",
]

OFFCUT_KEEP_COLOUR    = colors.HexColor("#16A34A")
OFFCUT_DISCARD_COLOUR = colors.HexColor("#DC2626")
OFFCUT_KEEP_MIN_MM    = 150

# Layout
PAGE_W       = A4[0]
LEFT_MARGIN  = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN   = 22 * mm
BOT_MARGIN   = 20 * mm
USABLE_W     = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN

BAR_LABEL_W = 16 * mm
CHIP_W      = 30 * mm
OFFCUT_W    = 26 * mm
CHIPS_AREA_W = USABLE_W - BAR_LABEL_W - OFFCUT_W
MAX_CHIPS   = max(1, int(CHIPS_AREA_W / CHIP_W))


def _item_colour(item_no: int) -> colors.Color:
    return colors.HexColor(ITEM_COLOURS[(item_no - 1) % len(ITEM_COLOURS)])


def _make_style(name, font="Helvetica", size=7.5, colour=None, bold=False, leading=10):
    return ParagraphStyle(
        name, fontName="Helvetica-Bold" if bold else font,
        fontSize=size, textColor=colour or colors.HexColor("#1A1A1A"),
        leading=leading, alignment=TA_LEFT,
    )


CHIP_S   = _make_style("chip", size=7.5)
BOLD_S   = _make_style("bold", bold=True, size=8)
HEAD_S   = _make_style("head", bold=True, size=9)


def _chip_cell(item_no: int, length_mm: float) -> Paragraph:
    """Coloured pill chip as a mini table."""
    label = Paragraph(f"<b>{item_no}</b> · {length_mm}", CHIP_S)
    t = Table([[label]], colWidths=[CHIP_W - 2 * mm], rowHeights=[10 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _item_colour(item_no)),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


def _offcut_cell(offcut_mm: int) -> Paragraph:
    is_keep = offcut_mm >= OFFCUT_KEEP_MIN_MM
    colour  = OFFCUT_KEEP_COLOUR if is_keep else OFFCUT_DISCARD_COLOUR
    label   = Paragraph(
        f"<b>Offcut {offcut_mm}</b>",
        _make_style("off", bold=True, size=8, colour=colors.white),
    )
    t = Table([[label]], colWidths=[OFFCUT_W - 2 * mm], rowHeights=[10 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colour),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


def _empty_cell() -> Paragraph:
    return Paragraph("", BOLD_S)


def _layout_bar_rows(bar_no: int, cuts: list, offcut_mm: int, max_chips: int) -> list:
    """
    Returns list of Tables — one per logical row of the bar.
    - First row: "Bar #N" label | chips | offcut
    - Continuation rows: "Bar #N (cont.)" label | chips | (offcut only on LAST row)
    """
    # Sort cuts by item_no
    sorted_cuts = sorted(cuts, key=lambda c: (c.get("item", 0), c.get("length_mm", 0)))
    chips = [(c["item"], c["length_mm"]) for c in sorted_cuts]

    # Split into chunks of max_chips
    rows_data = []   # list of (is_last, [(item_no, length_mm)] )
    i = 0
    while i < len(chips):
        chunk = chips[i : i + max_chips]
        is_last = (i + len(chunk) >= len(chips))
        rows_data.append((is_last, chunk))
        i += len(chunk)

    tables = []
    for ri, (is_last, chunk) in enumerate(rows_data):
        is_first = (ri == 0)
        is_last_row = is_last

        # Label cell
        if is_first:
            label = Paragraph(f"<b>Bar #{bar_no}</b>", BOLD_S)
        else:
            label = Paragraph(f"<b>Bar #{bar_no} (cont.)</b>", BOLD_S)

        # Chip cells
        chip_cells = [_chip_cell(item_no, length_mm) for item_no, length_mm in chunk]
        # Pad with empty cells to fill max_chips
        for _ in range(max_chips - len(chip_cells)):
            chip_cells.append(_empty_cell())

        # Offcut cell — only on last row
        if is_last_row:
            off_cell = _offcut_cell(offcut_mm)
        else:
            off_cell = _empty_cell()

        col_widths = [BAR_LABEL_W] + [CHIP_W] * max_chips + [OFFCUT_W]
        row_t = Table(
            [[label] + chip_cells + [off_cell]],
            colWidths=col_widths,
            rowHeights=[11 * mm],
        )
        row_t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",         (0, 0), (0, 0),    "LEFT"),
            ("LEFTPADDING",   (0, 0), (-1, -1),  1 * mm),
            ("RIGHTPADDING",  (0, 0), (-1, -1),   1 * mm),
            ("TOPPADDING",   (0, 0), (-1, -1),   0),
            ("BOTTOMPADDING",(0, 0), (-1, -1),   0),
            ("BACKGROUND",    (0, 0), (0, 0),    colors.HexColor("#E5E7EB")),
        ]))
        tables.append(row_t)

    return tables


def _parse_section_key(key: str):
    parts = [p.strip() for p in key.split("|")]
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2], ""
    elif len(parts) == 2:
        return parts[0], parts[1], "", ""
    return key, "", "", ""


class CuttingDiagramRenderer:
    def __init__(self, design):
        self.design   = design
        self.bar_plan = design.bar_plan

    def render(self) -> bytes:
        story, _ = self._build_story()
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,   bottomMargin=BOT_MARGIN,
        )
        job_name = self.design.name or ""
        job_no   = self.design.job_no or ""
        doc.build(
            story,
            onFirstPage=lambda c, d: _draw_page(c, d, job_name, job_no),
            onLaterPages=lambda c, d: _draw_page(c, d, job_name, job_no),
        )
        return buf.getvalue()

    def _build_story(self):
        story = []
        for section_key, bars in self.bar_plan.items():
            if not bars:
                continue

            extr, colour, colour_code, stock = _parse_section_key(section_key)
            stock_str = f" - {stock}" if stock else ""
            heading = Paragraph(
                f"<b>{extr}</b> – {colour} – {colour_code}{stock_str}",
                HEAD_S,
            )
            story.append(KeepTogether([heading, Spacer(1, 2 * mm)]))

            for bar in bars:
                rows = _layout_bar_rows(
                    bar.get("bar_no", "?"),
                    bar.get("cuts", []),
                    bar.get("offcut_mm", 0),
                    MAX_CHIPS,
                )
                for row_t in rows:
                    story.append(row_t)
                story.append(Spacer(1, 1.5 * mm))  # gap between bars
            story.append(Spacer(1, 6 * mm))  # gap between sections

        return story, 1


def _draw_page(c, d, job_name, job_no):
    w, h = A4
    c.saveState()

    # Header
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1A1A1A"))
    c.drawString(LEFT_MARGIN, h - 15 * mm, "CUTTING DIAGRAMS (Operator) — Mixed Items")
    c.setFont("Helvetica", 9)
    c.drawRightString(w - RIGHT_MARGIN, h - 15 * mm,
                      f"Job: {job_name}    Job No: {job_no}")

    c.setStrokeColor(colors.HexColor("#333333"))
    c.setLineWidth(0.5)
    c.line(LEFT_MARGIN, h - 17 * mm, w - RIGHT_MARGIN, h - 17 * mm)

    # Footer
    page = c.getPageNumber()
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawRightString(w - RIGHT_MARGIN, 10 * mm, f"Page {page}")

    c.restoreState()


def generate_cutting_diagram_pdf(design) -> bytes:
    return CuttingDiagramRenderer(design).render()
