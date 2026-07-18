#!/usr/bin/env python3
"""
One-off / repeatable: build print-friendly PDF from catalog CSV.
Removes columns: brand, visibility, status.
Usage:
  python3 build_catalog_print_pdf.py [input.csv] [output.pdf]
Defaults: catalog-data-spreadsheet4.csv -> catalog-data-spreadsheet4-print.pdf
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DROP = {"brand", "visibility", "status"}


def main() -> None:
    base = Path(__file__).resolve().parent
    in_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "catalog-data-spreadsheet4.csv"
    out_pdf = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "catalog-data-spreadsheet4-print.pdf"

    with open(in_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [c for c in reader.fieldnames if c and c not in DROP]
        rows_data = []
        for row in reader:
            rows_data.append([row.get(k, "") or "" for k in fieldnames])

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        name="Cell",
        parent=styles["Normal"],
        fontSize=6,
        leading=7,
        spaceAfter=0,
        spaceBefore=0,
    )
    header_style = ParagraphStyle(
        name="Hdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
    )

    def P(text: str, hdr: bool = False) -> Paragraph:
        t = escape(str(text).strip()) or " "
        return Paragraph(t.replace("\n", " "), header_style if hdr else cell_style)

    header_row = [P(h.replace("_", " "), hdr=True) for h in fieldnames]
    body = []
    for r in rows_data:
        body.append([P(c) for c in r])

    data = [header_row] + body

    page_w, page_h = landscape(A4)
    margin = 0.45 * inch
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=landscape(A4),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title="Catalog print view",
        author="Brian Streckfus",
    )

    usable = page_w - 2 * margin
    ncols = len(fieldnames)
    # Wider columns for text-heavy fields
    weights = {
        "id": 0.7,
        "title": 1.2,
        "description": 2.8,
        "availability": 0.6,
        "condition": 0.5,
        "price": 0.65,
        "link": 1.4,
        "image_link": 1.4,
        "google_product_category": 0.9,
        "fb_product_category": 0.9,
        "product_type": 1.0,
        "additional_image_link": 1.4,
    }
    wsum = sum(weights.get(h, 1.0) for h in fieldnames)
    col_widths = [usable * weights.get(h, 1.0) / wsum for h in fieldnames]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("FONTSIZE", (0, 1), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f8")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bdc3c7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story = [
        Paragraph(
            "<b>Sheet music catalog</b> &mdash; print view (brand / visibility / status columns omitted)",
            ParagraphStyle(
                name="Title",
                parent=styles["Heading1"],
                fontSize=11,
                leading=14,
                spaceAfter=8,
            ),
        ),
        Paragraph(
            f"Source: <i>{escape(in_csv.name)}</i> &mdash; {len(body)} listings",
            ParagraphStyle(name="Sub", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
        ),
        Spacer(1, 10),
        table,
    ]
    doc.build(story)
    print(f"Wrote {out_pdf} ({len(body)} rows, {ncols} columns)")


if __name__ == "__main__":
    main()
