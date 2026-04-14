"""SVG cross-section visualizer for the coil system.

Returns an SVG string that the results tab embeds via :func:`ui.html`.
The drawing is a professional schematic side-view with:
- Subtle grid background
- Proportional secondary, primary, topload, and ground plane
- Dimension lines with arrow markers
- Component labels
- Legend strip

Uses DESIGN.md visualization palette.
"""

from __future__ import annotations

from pyteslacoil.models.coil_design import ToploadType
from ui.state import AppState
from ui.theme import (
    TEXT_DIM,
    TEXT_MUTED,
    VIS_DIAGRAM_BG,
    VIS_GRID,
    VIS_GROUND,
    VIS_PRIMARY,
    VIS_SECONDARY,
    VIS_TOPLOAD,
)

CANVAS_W = 520
CANVAS_H = 520
PADDING = 50

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


def _dim_line(
    x1: float, y1: float, x2: float, y2: float, label: str, offset: float = 0
) -> str:
    """Render a dimension line with arrows and a label."""
    mx, my = (x1 + x2) / 2 + offset, (y1 + y2) / 2
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{TEXT_DIM}" stroke-width="1" stroke-dasharray="4,3" '
        f'marker-start="url(#arr-rev)" marker-end="url(#arr)"/>'
        f'<text x="{mx}" y="{my - 4}" font-size="10" fill="{TEXT_DIM}" '
        f'text-anchor="middle" font-family="\'JetBrains Mono\', monospace">{label}</text>'
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


def build(state: AppState) -> str:
    sec = state.design.secondary
    pri = state.design.primary
    top = state.design.topload

    # Determine bounding box across all elements (in meters).
    extents_x: list[float] = []
    extents_y: list[float] = [0.0]

    if sec is not None:
        extents_x += [-sec.radius_1, -sec.radius_2, sec.radius_1, sec.radius_2]
        extents_y += [sec.height_1, sec.height_2]
    if pri is not None:
        extents_x += [-pri.radius_2, pri.radius_2]
        extents_y += [pri.height_1, pri.height_2]
    if top is not None:
        if top.topload_type == ToploadType.TOROID and top.major_diameter:
            extents_x += [-0.5 * top.major_diameter, 0.5 * top.major_diameter]
            extents_y += [
                top.height - 0.5 * (top.minor_diameter or 0.0),
                top.height + 0.5 * (top.minor_diameter or 0.0),
            ]
        elif top.topload_type == ToploadType.SPHERE and top.sphere_diameter:
            extents_x += [-0.5 * top.sphere_diameter, 0.5 * top.sphere_diameter]
            extents_y += [
                top.height - 0.5 * top.sphere_diameter,
                top.height + 0.5 * top.sphere_diameter,
            ]

    if not extents_x:
        return (
            f'<div style="color: {TEXT_MUTED}; padding: 40px; text-align: center; '
            f'font-family: Inter, sans-serif;">No coil to draw yet.</div>'
        )

    x_min, x_max = min(extents_x), max(extents_x)
    y_min, y_max = min(extents_y), max(extents_y)
    span_y = max(y_max - y_min, 1e-6)

    # Symmetric horizontal centred on x=0.
    half = max(abs(x_min), abs(x_max)) * 1.15
    span_x = 2 * half

    draw_w = CANVAS_W - 2 * PADDING
    draw_h = CANVAS_H - 2 * PADDING - 30  # reserve 30px for legend
    scale = min(draw_w / span_x, draw_h / span_y)

    def sx(x: float) -> float:
        return CANVAS_W / 2 + x * scale

    def sy(y: float) -> float:
        return CANVAS_H - PADDING - 30 - (y - y_min) * scale

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

    # ── Secondary coil ─────────────────────────────────────────────
    if sec is not None:
        x1s, x2s = sx(-sec.radius_1), sx(sec.radius_1)
        y1s, y2s = sy(sec.height_2), sy(sec.height_1)
        w_rect = abs(x2s - x1s)
        h_rect = abs(y2s - y1s)
        parts.append(
            f'<rect x="{min(x1s, x2s)}" y="{min(y1s, y2s)}" '
            f'width="{w_rect}" height="{h_rect}" rx="2" '
            f'fill="{VIS_SECONDARY}" fill-opacity="0.45" '
            f'stroke="{VIS_SECONDARY}" stroke-width="1.5"/>'
        )
        # Label
        lx = sx(sec.radius_1) + 8
        ly = sy(0.5 * (sec.height_1 + sec.height_2))
        parts.append(
            f'<text x="{lx}" y="{ly}" font-size="11" fill="{VIS_SECONDARY}" '
            f'font-family="Inter, sans-serif" font-weight="500">Secondary</text>'
        )
        # Height dimension line (right side)
        dim_x = sx(sec.radius_1) + 24
        height_m = abs(sec.height_2 - sec.height_1)
        parts.append(_dim_line(dim_x, y1s, dim_x, y2s, f"{height_m * 100:.1f}cm"))

    # ── Primary coil ───────────────────────────────────────────────
    if pri is not None:
        if abs(pri.height_2 - pri.height_1) < 1e-6:
            # Flat spiral
            y_band = sy(pri.height_1)
            xa_l = sx(-pri.radius_2)
            xa_r = sx(pri.radius_2)
            xb_l = sx(-pri.radius_1)
            xb_r = sx(pri.radius_1)
            # Draw as a thick band from r1 to r2 on each side
            for xl, xr in [(xa_l, xb_l), (xb_r, xa_r)]:
                parts.append(
                    f'<line x1="{xl}" y1="{y_band}" x2="{xr}" y2="{y_band}" '
                    f'stroke="{VIS_PRIMARY}" stroke-width="6" stroke-linecap="round" '
                    f'opacity="0.8"/>'
                )
            # Radius dimension (below)
            dim_y = y_band + 20
            parts.append(
                _dim_line(
                    sx(-pri.radius_2), dim_y, sx(pri.radius_2), dim_y,
                    f"\u00d8{pri.radius_2 * 200:.1f}cm"
                )
            )
        else:
            # Helical / conical trapezoid
            x_top_l, x_top_r = sx(-pri.radius_2), sx(pri.radius_2)
            x_bot_l, x_bot_r = sx(-pri.radius_1), sx(pri.radius_1)
            y_top, y_bot = sy(pri.height_2), sy(pri.height_1)
            d = (
                f"M {x_bot_l} {y_bot} "
                f"L {x_top_l} {y_top} "
                f"L {x_top_r} {y_top} "
                f"L {x_bot_r} {y_bot} Z"
            )
            parts.append(
                f'<path d="{d}" fill="{VIS_PRIMARY}" fill-opacity="0.35" '
                f'stroke="{VIS_PRIMARY}" stroke-width="1.5"/>'
            )
        # Label
        parts.append(
            f'<text x="{sx(pri.radius_2) + 8}" y="{sy(pri.height_1) + 4}" '
            f'font-size="11" fill="{VIS_PRIMARY}" '
            f'font-family="Inter, sans-serif" font-weight="500">Primary</text>'
        )

    # ── Topload ────────────────────────────────────────────────────
    if top is not None:
        if top.topload_type == ToploadType.TOROID and top.major_diameter and top.minor_diameter:
            R = 0.5 * top.major_diameter
            r = 0.5 * top.minor_diameter
            for cx_m in (-R + r, R - r):
                cx, cy = sx(cx_m), sy(top.height)
                rx = ry = r * scale
                parts.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                    f'fill="{VIS_TOPLOAD}" fill-opacity="0.4" '
                    f'stroke="{VIS_TOPLOAD}" stroke-width="1.5"/>'
                )
            # Connecting bar between toroid halves
            parts.append(
                f'<line x1="{sx(-R + r)}" y1="{sy(top.height) - r * scale}" '
                f'x2="{sx(R - r)}" y2="{sy(top.height) - r * scale}" '
                f'stroke="{VIS_TOPLOAD}" stroke-width="1" stroke-opacity="0.4"/>'
            )
            parts.append(
                f'<line x1="{sx(-R + r)}" y1="{sy(top.height) + r * scale}" '
                f'x2="{sx(R - r)}" y2="{sy(top.height) + r * scale}" '
                f'stroke="{VIS_TOPLOAD}" stroke-width="1" stroke-opacity="0.4"/>'
            )
            parts.append(
                f'<text x="{sx(R) + 8}" y="{sy(top.height)}" font-size="11" '
                f'fill="{VIS_TOPLOAD}" font-family="Inter, sans-serif" '
                f'font-weight="500">Toroid</text>'
            )
        elif top.topload_type == ToploadType.SPHERE and top.sphere_diameter:
            r = 0.5 * top.sphere_diameter * scale
            cx, cy = sx(0.0), sy(top.height)
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{VIS_TOPLOAD}" fill-opacity="0.4" '
                f'stroke="{VIS_TOPLOAD}" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text x="{cx + r + 8}" y="{cy}" font-size="11" '
                f'fill="{VIS_TOPLOAD}" font-family="Inter, sans-serif" '
                f'font-weight="500">Sphere</text>'
            )

    # ── Legend ──────────────────────────────────────────────────────
    parts.append(_legend())

    parts.append("</svg>")
    return "".join(parts)
