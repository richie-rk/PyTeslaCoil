"""Shared card and result display components."""

from __future__ import annotations

import math

from nicegui import ui

from pyteslacoil.ui.theme import (
    ACCENT,
    BAD,
    CARD_STYLE,
    GOOD,
    LABEL_CLASS,
    LABEL_STYLE,
    MONO_STACK,
    SECTION_TITLE_CLASS,
    SECTION_TITLE_STYLE,
    SURFACE,
    SURFACE_BORDER,
    TEXT_DIM,
    TEXT_MUTED,
    VALUE_CLASS,
    VALUE_STYLE,
    WARN,
)

DASH = "—"


def fmt(value: float | None, spec: str, suffix: str = "") -> str:
    """Format a value for display; ``None`` and non-finite values show as a dash."""
    if value is None or not math.isfinite(value):
        return DASH
    text = format(value, spec)
    return f"{text} {suffix}" if suffix else text


def coupling_quality(k: float) -> tuple[str, str]:
    """``(label, color)`` rating a coupling coefficient for a spark-gap coil."""
    if 0.10 <= k <= 0.25:
        return "ok", GOOD
    if 0.05 <= k < 0.10 or 0.25 < k <= 0.30:
        return "marginal", WARN
    return "out of range", BAD


def section_card(title: str, icon: str | None = None) -> ui.card:
    """A styled card with a section title header; use it as a context manager.

    Usage::

        with section_card("Secondary Coil", "bolt"):
            ui.number(...)
    """
    card = ui.card().classes("w-full").style(CARD_STYLE)
    with card:
        with ui.row().classes("items-center gap-2 mb-4"):
            if icon:
                ui.icon(icon).classes("text-lg").style(f"color: {ACCENT};")
            ui.label(title).classes(SECTION_TITLE_CLASS).style(SECTION_TITLE_STYLE)
    return card


def metric_card(
    title: str,
    value: str = DASH,
    unit: str = "",
    border_color: str = ACCENT,
) -> tuple[ui.label, ui.label]:
    """Headline metric card with a colored top border.

    Returns ``(value_label, unit_label)`` so callers can update them.
    """
    with ui.card().classes("flex-1 min-w-[140px] sm:min-w-[200px]").style(
        f"background: {SURFACE}; border: 1px solid {SURFACE_BORDER}; "
        f"border-top: 4px solid {border_color}; border-radius: 8px; "
        f"padding: 20px; text-align: center;"
    ):
        ui.label(title).style(f"color: {TEXT_DIM}; font-size: 12px;")
        val_lbl = ui.label(value).style(
            f"color: {border_color}; font-size: 28px; font-weight: 700; "
            f"font-family: {MONO_STACK};"
        )
        unit_lbl = ui.label(unit).style(f"color: {TEXT_MUTED}; font-size: 14px;")
    return val_lbl, unit_lbl


def results_grid() -> ui.element:
    """Label/value grid — single column on mobile, two columns from sm up."""
    return ui.element("div").classes("grid grid-cols-1 sm:grid-cols-2 w-full gap-x-4 gap-y-3")


def result_row(grid: ui.element, name: str) -> ui.label:
    """Add a label/value row inside an existing results_grid. Returns the value label."""
    with grid:
        ui.label(name).classes(LABEL_CLASS).style(LABEL_STYLE)
        lbl = ui.label(DASH).classes(VALUE_CLASS).style(VALUE_STYLE)
    return lbl


def result_rows(grid: ui.element, names: dict[str, str]) -> dict[str, ui.label]:
    """Add several rows; ``names`` maps a key to its label text."""
    return {key: result_row(grid, name) for key, name in names.items()}


def clear_rows(rows: dict[str, ui.label]) -> None:
    for label in rows.values():
        label.text = DASH
