from __future__ import annotations

import io
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def create_summary_pdf(summary: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(1 * inch, 10 * inch, "DhanRakshak Filing Summary")
    y = 9.5 * inch
    for key, value in summary.items():
        pdf.drawString(1 * inch, y, f"{key}: {value}")
        y -= 0.3 * inch
        if y < 1 * inch:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 10 * inch
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def create_certificate_pdf(full_name: str, tx_hash: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(4.25 * inch, 6 * inch, full_name)
    pdf.drawCentredString(4.25 * inch, 5.5 * inch, tx_hash)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def create_heatmap_pdf(notes: str = "Heatmap placeholder") -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(1 * inch, 10 * inch, "Heatmap")
    pdf.drawString(1 * inch, 9.5 * inch, notes)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
