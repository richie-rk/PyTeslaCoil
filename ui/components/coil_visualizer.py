"""SVG cross-section visualizer for the coil system.

Returns an SVG string that the results tab embeds via :func:`ui.html`.
The drawing is intentionally schematic — it shows a side view of the
secondary, primary, topload, and a ground plane, all proportional to
their actual physical dimensions.
"""

from __future__ import annotations

from pyteslacoil.models.coil_design import ToploadType
from ui.state import AppState

CANVAS_W = 480
CANVAS_H = 480
PADDING = 30


def build(state: AppState) -> str:
    sec = state.design.secondary
    pri = state.design.primary
    top = state.design.topload

    # Determine the bounding box across all elements (in meters).
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
        return "<div class='text-slate-400'>No coil to draw yet.</div>"

    x_min, x_max = min(extents_x), max(extents_x)
    y_min, y_max = min(extents_y), max(extents_y)
    span_x = max(x_max - x_min, 1e-6)
    span_y = max(y_max - y_min, 1e-6)

    # Symmetric horizontal — centre on x=0.
    half = max(abs(x_min), abs(x_max)) * 1.1
    span_x = 2 * half

    scale = min(
        (CANVAS_W - 2 * PADDING) / span_x,
        (CANVAS_H - 2 * PADDING) / span_y,
    )

    def sx(x: float) -> float:
        return CANVAS_W / 2 + x * scale

    def sy(y: float) -> float:
        # Flip — y grows upward in physics, downward in SVG.
        return CANVAS_H - PADDING - (y - y_min) * scale

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
        f'class="w-full h-auto bg-slate-900 rounded-lg">',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#0B132B"/>',
    ]

    # Ground plane line.
    gy = sy(0.0)
    parts.append(
        f'<line x1="{PADDING}" y1="{gy}" x2="{CANVAS_W - PADDING}" y2="{gy}" '
        'stroke="#9DA9B8" stroke-width="2" stroke-dasharray="6,4"/>'
    )
    parts.append(
        f'<text x="{CANVAS_W - PADDING}" y="{gy - 4}" font-size="10" '
        'fill="#9DA9B8" text-anchor="end">ground</text>'
    )

    # Secondary — shaded vertical rectangle.
    if sec is not None:
        x1, x2 = sx(-sec.radius_1), sx(sec.radius_1)
        y1, y2 = sy(sec.height_2), sy(sec.height_1)
        parts.append(
            f'<rect x="{min(x1, x2)}" y="{min(y1, y2)}" '
            f'width="{abs(x2 - x1)}" height="{abs(y2 - y1)}" '
            'fill="#0077B6" fill-opacity="0.55" stroke="#90E0EF" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{sx(sec.radius_1) + 6}" y="{sy(0.5 * (sec.height_1 + sec.height_2))}" '
            'font-size="11" fill="#90E0EF">secondary</text>'
        )

    # Primary — flat spiral, helical, or conical.
    if pri is not None:
        if abs(pri.height_2 - pri.height_1) < 1e-6:
            # Flat spiral: thin horizontal band at h1, from r1 to r2 (mirrored).
            y_band = sy(pri.height_1)
            for sign in (-1.0, 1.0):
                xa = sx(sign * pri.radius_1)
                xb = sx(sign * pri.radius_2)
                parts.append(
                    f'<line x1="{min(xa, xb)}" y1="{y_band}" '
                    f'x2="{max(xa, xb)}" y2="{y_band}" '
                    'stroke="#FFD166" stroke-width="6" stroke-linecap="round"/>'
                )
        else:
            # Helical / conical: trapezoid outline.
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
                f'<path d="{d}" fill="#FFD166" fill-opacity="0.4" '
                'stroke="#FFD166" stroke-width="2"/>'
            )
        parts.append(
            f'<text x="{sx(pri.radius_2) + 6}" y="{sy(pri.height_1) + 4}" '
            'font-size="11" fill="#FFD166">primary</text>'
        )

    # Topload.
    if top is not None:
        if top.topload_type == ToploadType.TOROID and top.major_diameter and top.minor_diameter:
            R = 0.5 * top.major_diameter
            r = 0.5 * top.minor_diameter
            # Draw two circles (the side view of a toroid is two ellipses).
            for cx_m in (-R + r, R - r):
                cx, cy = sx(cx_m), sy(top.height)
                rx = ry = r * scale
                parts.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                    'fill="#06D6A0" fill-opacity="0.5" stroke="#06D6A0" stroke-width="1.5"/>'
                )
            parts.append(
                f'<text x="{sx(R) + 8}" y="{sy(top.height)}" font-size="11" '
                'fill="#06D6A0">toroid</text>'
            )
        elif top.topload_type == ToploadType.SPHERE and top.sphere_diameter:
            r = 0.5 * top.sphere_diameter * scale
            cx, cy = sx(0.0), sy(top.height)
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                'fill="#06D6A0" fill-opacity="0.5" stroke="#06D6A0" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text x="{cx + r + 6}" y="{cy}" font-size="11" '
                'fill="#06D6A0">sphere</text>'
            )

    parts.append("</svg>")
    return "".join(parts)
