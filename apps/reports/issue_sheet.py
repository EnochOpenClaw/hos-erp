# reports/issue_sheet.py
"""
Issue Sheet PDF — summarises the optimized cutting list for stock issue.

Groups by extrusion + colour + finish (from section heading).
Per section: name, colour, colour code, then per-stock-length:
  - qty needed (full bars used) = number of bars of that stock length
  - extrusion type, stock length, total qty

Does NOT include offcuts.
"""
from io import BytesIO
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

LEFT_MARGIN  = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN   = 22 * mm
BOT_MARGIN   = 20 * mm
USABLE_W     = A4[0] - LEFT_MARGIN - RIGHT_MARGIN

# Colours
HEADER_BG   = colors.HexColor("#1A1A1A")
HEADER_FG   = colors.white
SUBHEAD_BG  = colors.HexColor("#E5E7EB")
ROW_ALT     = colors.HexColor("#F9FAFB")
GREEN_ACCENT= colors.HexColor("#16A34A")


def _parse_key(key: str):
    parts = [p.strip() for p in key.split("|")]
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2], ""
    elif len(parts) == 2:
        return parts[0], parts[1], "", ""
    return key, "", "", ""


def _build_issue_sheet(design, job_name, job_no, issue_no, division_code) -> bytes:
    # Aggregate: (extrusion, colour, colour_code, stock_len) -> bar count
    section_data = defaultdict(lambda: defaultdict(int))
    # section_data[section_key][stock_len] = qty

    for section_key, bars in design.bar_plan.items():
        if not bars:
            continue
        extr, colour, colour_code, _ = _parse_key(section_key)
        for bar in bars:
            stock_len = bar.get("stock_len", 0)
            section_data[(extr, colour, colour_code)][stock_len] += 1

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOT_MARGIN,
    )

    styles = {
        "title":   ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=14,
                                  textColor=colors.HexColor("#1A1A1A"), leading=18),
        "sub":     ParagraphStyle("s", fontName="Helvetica", fontSize=9,
                                  textColor=colors.HexColor("#555555"), leading=12),
        "section": ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=10,
                                  textColor=colors.HexColor("#1A1A1A"), leading=13),
        "colhdr":  ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=colors.white, leading=10, alignment=TA_CENTER),
        "body":    ParagraphStyle("b", fontName="Helvetica", fontSize=8,
                                  textColor=colors.HexColor("#1A1A1A"), leading=10),
        "bold":    ParagraphStyle("bo", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=colors.HexColor("#1A1A1A"), leading=10),
        "note":    ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=7.5,
                                  textColor=colors.HexColor("#666666"), leading=10),
    }

    story = []

    # ── Title block ───────────────────────────────────────────────────────────
    story.append(Paragraph("ISSUE SHEET", styles["title"]))
    story.append(Spacer(1, 2 * mm))

    # Meta table
    meta_data = [
        [Paragraph("<b>Job:</b>", styles["bold"]), Paragraph(job_name, styles["body"]),
         Paragraph("<b>Job No:</b>", styles["bold"]), Paragraph(job_no, styles["body"])],
        [Paragraph("<b>Issue No:</b>", styles["bold"]), Paragraph(issue_no, styles["body"]),
         Paragraph("<b>Division:</b>", styles["bold"]), Paragraph(division_code, styles["body"])],
    ]
    meta_t = Table(meta_data, colWidths=[22*mm, 80*mm, 22*mm, USABLE_W-124*mm])
    meta_t.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",  (0,0),(-1,-1), 1*mm),
        ("BOTTOMPADDING",(0,0),(-1,-1), 1*mm),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 2*mm),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1A1A1A")))
    story.append(Spacer(1, 4 * mm))

    # ── Per-section ───────────────────────────────────────────────────────────
    total_items = 0
    for (extr, colour, colour_code), stock_map in sorted(section_data.items()):
        total_qty = sum(stock_map.values())
        total_items += total_qty

        # Section heading
        colour_str = f"{colour}" + (f" ({colour_code})" if colour_code else "")
        story.append(Paragraph(
            f"<b>{extr}</b> — {colour_str}",
            styles["section"],
        ))
        story.append(Spacer(1, 1 * mm))

        # Column headers
        hdr_data = [[
            Paragraph("Stock Length (mm)", styles["colhdr"]),
            Paragraph("Quantity", styles["colhdr"]),
            Paragraph("Finish", styles["colhdr"]),
            Paragraph("Colour", styles["colhdr"]),
        ]]
        hdr_t = Table(hdr_data, colWidths=[60*mm, 25*mm, 40*mm, USABLE_W-125*mm])
        hdr_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), HEADER_BG),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
            ("ALIGN",        (0,0),(-1,-1), "CENTER"),
            ("TOPPADDING",  (0,0),(-1,-1), 2*mm),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2*mm),
            ("LEFTPADDING", (0,0),(-1,-1), 2*mm),
        ]))
        story.append(hdr_t)

        # Data rows
        for si, (stock_len, qty) in enumerate(sorted(stock_map.items())):
            bg = ROW_ALT if si % 2 == 1 else colors.white
            finish = "Powdercoated" if colour.lower() != "mill" else "Mill"
            row_data = [[
                Paragraph(str(stock_len), styles["body"]),
                Paragraph(str(qty), styles["body"]),
                Paragraph(finish, styles["body"]),
                Paragraph(colour, styles["body"]),
            ]]
            row_t = Table(row_data, colWidths=[60*mm, 25*mm, 40*mm, USABLE_W-125*mm])
            row_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0), bg),
                ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
                ("ALIGN",        (1,0),(-1,0), "CENTER"),
                ("TOPPADDING",  (0,0),(-1,-1), 2*mm),
                ("BOTTOMPADDING",(0,0),(-1,-1), 2*mm),
                ("LEFTPADDING", (0,0),(-1,-1), 2*mm),
                ("GRID",        (0,0),(-1,-1), 0.25, colors.HexColor("#D1D5DB")),
            ]))
            story.append(row_t)

        # Section subtotal
        story.append(Paragraph(
            f"Subtotal: <b>{total_qty} bars</b>  |  "
            f"{colour}  |  {extr}",
            styles["note"],
        ))
        story.append(Spacer(1, 5 * mm))

    # ── Grand total ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF")))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"<b>Total items to issue: {total_items} bars</b>",
        ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=10,
                       textColor=GREEN_ACCENT, leading=13),
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "Verify quantities against stock before issuing. "
        "Offcuts are NOT included — these remain in store.",
        styles["note"],
    ))

    doc.build(story)
    return buf.getvalue()


def generate_issue_sheet_pdf(design, job_name="", job_no="", issue_no="", division_code="") -> bytes:
    return _build_issue_sheet(design, job_name, job_no, issue_no, division_code)
