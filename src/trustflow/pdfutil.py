from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def text_to_pdf_bytes(title: str, text: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 60, title[:80])
    c.setFont("Helvetica", 9)
    y = height - 90
    for raw_line in text.splitlines() or [text]:
        words = raw_line.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if c.stringWidth(candidate, "Helvetica", 9) > width - 100:
                c.drawString(50, y, line)
                y -= 13
                line = word
                if y < 55:
                    c.showPage(); c.setFont("Helvetica", 9); y = height - 55
            else:
                line = candidate
        if line:
            c.drawString(50, y, line)
            y -= 13
        if y < 55:
            c.showPage(); c.setFont("Helvetica", 9); y = height - 55
    c.save()
    return buf.getvalue()
