"""SVG cross-section visualizer for the coil system.

Returns an SVG string that the results tab embeds. The drawing is a
schematic side view with:

- a subtle grid background
- proportional secondary (conical secondaries as trapezoids), primary,
  topload and ground plane
- dimension lines with arrow markers, labelled in the design's unit system
- component labels and a legend strip
"""

from __future__ import annotations

from pyteslacoil.models import CoilDesign, PrimaryInput, ToploadType
from pyteslacoil.ui.theme import (
    TEXT_DIM,
    TEXT_MUTED,
    VIS_DIAGRAM_BG,
    VIS_GRID,
    VIS_GROUND,
    VIS_PRIMARY,
    VIS_SECONDARY,
    VIS_TOPLOAD,
)
from pyteslacoil.units import length_in, length_symbol, lengths_equal

CANVAS_W = 520
CANVAS_H = 520
PADDING = 50
LEGEND_H = 30

# Arrow marker definition for dimension lines.
_DEFS = f"""
<defs>
  <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6 Z" fill="{TEXT_DIM}"/>
  </marker>
  <marker id="arr-rev" markerWidth="8" markerHeight="6" refX="0" refY="3" orient="auto">
    <path d="M8,0 L0,3 L8,6 Z" fill="{TEXT_DIM}"/>
  </marker>
</defs>
"""


def _grid_lines() -> str:
    """Generate faint grid lines across the diagram area."""
    lines: list[str] = []
    step = 40
    for x in range(PADDING, CANVAS_W - PADDING + 1, step):
        lines.append(
            f'<line x1="{x}" y1="{PADDING}" x2="{x}" y2="{CANVAS_H - PADDING}" '
            f'stroke="{VIS_GRID}" stroke-width="0.5"/>'
        )
    for y in range(PADDING, CANVAS_H - PADDING + 1, step):
        lines.append(
            f'<line x1="{PADDING}" y1="{y}" x2="{CANVAS_W - PADDING}" y2="{y}" '
            f'stroke="{VIS_GRID}" stroke-width="0.5"/>'
        )
    return "".join(lines)


def _dim_line(x1: float, y1: float, x2: float, y2: float, label: str, offset: float = 0) -> str:
    """Render a dimension line with arrows and a label."""
    mx, my = (x1 + x2) / 2 + offset, (y1 + y2) / 2
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{TEXT_DIM}" stroke-width="1" stroke-dasharray="4,3" '
        f'marker-start="url(#arr-rev)" marker-end="url(#arr)"/>'
        f'<text x="{mx}" y="{my - 4}" font-size="10" fill="{TEXT_DIM}" '
        f'text-anchor="middle" font-family="\'JetBrains Mono\', monospace">{label}</text>'
    )


def _label(x: float, y: float, text: str, color: str) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="11" fill="{color}" '
        f'font-family="Inter, sans-serif" font-weight="500">{text}</text>'
    )


def _legend() -> str:
    """Component legend strip at the bottom."""
    items = [
        (VIS_SECONDARY, "Secondary"),
        (VIS_PRIMARY, "Primary"),
        (VIS_TOPLOAD, "Topload"),
        (VIS_GROUND, "Ground"),
    ]
    parts: list[str] = []
    x = PADDING
    y = CANVAS_H - 14
    for color, name in items:
        parts.append(
            f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" '
            f'fill="{color}" fill-opacity="0.8"/>'
        )
        parts.append(
            f'<text x="{x + 16}" y="{y + 10}" font-size="11" fill="{TEXT_DIM}" '
            f'font-family="Inter, sans-serif">{name}</text>'
        )
        x += len(name) * 7 + 36
    return "".join(parts)


def build(design: CoilDesign, primary: PrimaryInput | None = None) -> str:
    """SVG cross-section of ``design``; ``primary`` overrides the drawn primary
    (e.g. the auto-tuned geometry)."""
    sec = design.secondary
    pri = primary or design.primary
    top = design.topload
    unit = design.unit_system.value
    symbol = length_symbol(unit)

    def length_label(value_m: float) -> str:
        return f"{length_in(value_m, unit):.1f} {symbol}"

    # Determine bounding box across all elements (in meters).
    extents_x: list[float] = []
    extents_y: list[float] = [0.0]

    if sec is not None:
        r_max = max(sec.radius_1, sec.radius_2)
        extents_x += [-r_max, r_max]
        extents_y += [sec.height_1, sec.height_2]
    if pri is not None:
        r_max = max(pri.radius_1, pri.radius_2)
        extents_x += [-r_max, r_max]
        extents_y += [pri.height_1, pri.height_2]
    if top is not None and top.height is not None:
        if top.topload_type == ToploadType.TOROID and top.major_diameter and top.minor_diameter:
            extents_x += [-0.5 * top.major_diameter, 0.5 * top.major_diameter]
            extents_y += [top.height - 0.5 * top.minor_diameter, top.height + 0.5 * top.minor_diameter]
        elif top.topload_type == ToploadType.SPHERE and top.sphere_diameter:
            extents_x += [-0.5 * top.sphere_diameter, 0.5 * top.sphere_diameter]
            extents_y += [top.height - 0.5 * top.sphere_diameter, top.height + 0.5 * top.sphere_diameter]

    if not extents_x:
        return (
            f'<div style="color: {TEXT_MUTED}; padding: 40px; text-align: center; '
            f'font-family: Inter, sans-serif;">No coil to draw yet.</div>'
        )

    y_min, y_max = min(extents_y), max(extents_y)
    span_y = max(y_max - y_min, 1e-6)

    # Symmetric horizontal centred on x=0.
    half = max(abs(x) for x in extents_x) * 1.15
    span_x = 2 * half

    draw_w = CANVAS_W - 2 * PADDING
    draw_h = CANVAS_H - 2 * PADDING - LEGEND_H
    scale = min(draw_w / span_x, draw_h / span_y)

    def sx(x: float) -> float:
        return CANVAS_W / 2 + x * scale

    def sy(y: float) -> float:
        return CANVAS_H - PADDING - LEGEND_H - (y - y_min) * scale

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
        f'class="w-full h-auto" style="border-radius: 8px;">',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{VIS_DIAGRAM_BG}" rx="8"/>',
        _DEFS,
        _grid_lines(),
    ]

    # ── Ground plane ───────────────────────────────────────────────
    gy = sy(0.0)
    parts.append(
        f'<line x1="{PADDING}" y1="{gy}" x2="{CANVAS_W - PADDING}" y2="{gy}" '
        f'stroke="{VIS_GROUND}" stroke-width="2" stroke-dasharray="8,4"/>'
    )
    parts.append(
        f'<text x="{CANVAS_W - PADDING}" y="{gy - 6}" font-size="10" '
        f'fill="{VIS_GROUND}" text-anchor="end" '
        f'font-family="Inter, sans-serif">GND</text>'
    )

    # ── Secondary coil (trapezoid: bottom radius_1, top radius_2) ──
    if sec is not None:
        y_bot, y_top = sy(sec.height_1), sy(sec.height_2)
        outline = (
            f"M {sx(-sec.radius_1)} {y_bot} L {sx(-sec.radius_2)} {y_top} "
            f"L {sx(sec.radius_2)} {y_top} L {sx(sec.radius_1)} {y_bot} Z"
        )
        parts.append(
            f'<path d="{outline}" fill="{VIS_SECONDARY}" fill-opacity="0.45" '
            f'stroke="{VIS_SECONDARY}" stroke-width="1.5" stroke-linejoin="round"/>'
        )
        r_right = max(sec.radius_1, sec.radius_2)
        parts.append(
            _label(sx(r_right) + 8, sy(0.5 * (sec.height_1 + sec.height_2)), "Secondary", VIS_SECONDARY)
        )
        # Height dimension line (right side)
        dim_x = sx(r_right) + 24
        parts.append(_dim_line(dim_x, y_bot, dim_x, y_top, length_label(sec.height_2 - sec.height_1)))

    # ── Primary coil ───────────────────────────────────────────────
    if pri is not None:
        r_outer = max(pri.radius_1, pri.radius_2)
        if lengths_equal(pri.height_1, pri.height_2):
            # Flat spiral: a thick band from the inner to the outer radius on each side.
            r_inner = min(pri.radius_1, pri.radius_2)
            y_band = sy(pri.height_1)
            for xl, xr in [(sx(-r_outer), sx(-r_inner)), (sx(r_inner), sx(r_outer))]:
                parts.append(
                    f'<line x1="{xl}" y1="{y_band}" x2="{xr}" y2="{y_band}" '
                    f'stroke="{VIS_PRIMARY}" stroke-width="6" stroke-linecap="round" '
                    f'opacity="0.8"/>'
                )
            dim_y = y_band + 20
            parts.append(
                _dim_line(sx(-r_outer), dim_y, sx(r_outer), dim_y, f"Ø{length_label(2 * r_outer)}")
            )
        else:
            # Helical / conical trapezoid from (radius_1, height_1) to (radius_2, height_2).
            y_start, y_end = sy(pri.height_1), sy(pri.height_2)
            outline = (
                f"M {sx(-pri.radius_1)} {y_start} L {sx(-pri.radius_2)} {y_end} "
                f"L {sx(pri.radius_2)} {y_end} L {sx(pri.radius_1)} {y_start} Z"
            )
            parts.append(
                f'<path d="{outline}" fill="{VIS_PRIMARY}" fill-opacity="0.35" '
                f'stroke="{VIS_PRIMARY}" stroke-width="1.5"/>'
            )
        parts.append(_label(sx(r_outer) + 8, sy(min(pri.height_1, pri.height_2)) + 4, "Primary", VIS_PRIMARY))

    # ── Topload ────────────────────────────────────────────────────
    if top is not None and top.height is not None:
        cy = sy(top.height)
        if top.topload_type == ToploadType.TOROID and top.major_diameter and top.minor_diameter:
            big_r = 0.5 * top.major_diameter
            r = 0.5 * top.minor_diameter
            for cx_m in (-big_r + r, big_r - r):
                parts.append(
                    f'<ellipse cx="{sx(cx_m)}" cy="{cy}" rx="{r * scale}" ry="{r * scale}" '
                    f'fill="{VIS_TOPLOAD}" fill-opacity="0.4" '
                    f'stroke="{VIS_TOPLOAD}" stroke-width="1.5"/>'
                )
            # Connecting lines between the toroid halves.
            for dy in (-r * scale, r * scale):
                parts.append(
                    f'<line x1="{sx(-big_r + r)}" y1="{cy + dy}" x2="{sx(big_r - r)}" y2="{cy + dy}" '
                    f'stroke="{VIS_TOPLOAD}" stroke-width="1" stroke-opacity="0.4"/>'
                )
            parts.append(_label(sx(big_r) + 8, cy, "Toroid", VIS_TOPLOAD))
        elif top.topload_type == ToploadType.SPHERE and top.sphere_diameter:
            r_px = 0.5 * top.sphere_diameter * scale
            parts.append(
                f'<circle cx="{sx(0.0)}" cy="{cy}" r="{r_px}" '
                f'fill="{VIS_TOPLOAD}" fill-opacity="0.4" '
                f'stroke="{VIS_TOPLOAD}" stroke-width="1.5"/>'
            )
            parts.append(_label(sx(0.0) + r_px + 8, cy, "Sphere", VIS_TOPLOAD))

    # ── Legend ──────────────────────────────────────────────────────
    parts.append(_legend())

    parts.append("</svg>")
    return "".join(parts)
