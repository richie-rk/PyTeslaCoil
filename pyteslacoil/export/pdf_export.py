"""PDF export — the consolidated text report rendered with reportlab.

The report is laid out in a monospaced font and continues onto further
pages when it does not fit on one; long lines are wrapped, not truncated.
"""

from __future__ import annotations

import textwrap
from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from pyteslacoil.export.consolidated import to_text
from pyteslacoil.models import CoilDesign, FullSystemOutput

_MARGIN = 36
_FONT = "Courier"
_FONT_SIZE = 9
_LINE_HEIGHT = 11
_COURIER_ADVANCE_EM = 0.6  # every Courier glyph is 0.6 em wide

# reportlab's built-in fonts only cover the WinAnsi (cp1252) character set.
_REPLACEMENTS = {
    "Ω": "ohm",
    "≈": "~",
    "≥": ">=",
    "≤": "<=",
    "→": "->",
    "√": "sqrt",
    "π": "pi",
    "₀": "0",
}


def pdf_safe(text: str) -> str:
    """Make ``text`` drawable with the built-in PDF fonts."""
    for symbol, replacement in _REPLACEMENTS.items():
        text = text.replace(symbol, replacement)
    return text.encode("cp1252", errors="replace").decode("cp1252")


def to_pdf_bytes(design: CoilDesign, outputs: FullSystemOutput) -> bytes:
    title, *body = pdf_safe(to_text(design, outputs)).splitlines()

    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=LETTER)
    pdf.setTitle(title)
    width, height = LETTER
    max_chars = int((width - 2 * _MARGIN) / (_COURIER_ADVANCE_EM * _FONT_SIZE))

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(_MARGIN, height - _MARGIN, title)
    pdf.setFont(_FONT, _FONT_SIZE)
    y = height - _MARGIN - 24
    for raw_line in body:
        for line in textwrap.wrap(raw_line, max_chars, subsequent_indent=" " * 4) or [""]:
            if y < _MARGIN:
                pdf.showPage()
                pdf.setFont(_FONT, _FONT_SIZE)
                y = height - _MARGIN
            pdf.drawString(_MARGIN, y, line)
            y -= _LINE_HEIGHT

    pdf.save()
    return buf.getvalue()
