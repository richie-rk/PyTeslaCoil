"""PDF export — single-page design summary using reportlab.

reportlab is an *optional* dependency (declared in the ``pdf`` extra of
``pyproject.toml``). If it isn't installed, calling :func:`to_pdf_bytes`
raises an :class:`ImportError` with an actionable message.
"""

from __future__ import annotations

from pyteslacoil.export.consolidated import to_text
from pyteslacoil.models import CoilDesign, FullSystemOutput


def to_pdf_bytes(design: CoilDesign, outputs: FullSystemOutput) -> bytes:
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover - optional dep
        raise ImportError(
            "PDF export requires reportlab. Install with `pip install reportlab` "
            "or `pip install pyteslacoil[pdf]`."
        ) from exc

    from io import BytesIO

    text = to_text(design, outputs)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)

    width, height = LETTER
    margin = 36
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, f"PyTeslaCoil — {design.name}")

    c.setFont("Courier", 9)
    y = height - margin - 24
    line_height = 11
    for raw_line in text.splitlines():
        if y < margin:
            c.showPage()
            c.setFont("Courier", 9)
            y = height - margin
        c.drawString(margin, y, raw_line[:110])
        y -= line_height

    c.save()
    return buf.getvalue()
