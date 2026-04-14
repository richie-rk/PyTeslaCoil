"""Shared card and result display components using DESIGN.md tokens."""

from __future__ import annotations

from nicegui import ui

from ui.theme import (
    ACCENT,
    CARD_STYLE,
    LABEL_STYLE,
    MONO_STACK,
    SECTION_TITLE_STYLE,
    SURFACE,
    SURFACE_BORDER,
    TEXT_DIM,
    TEXT_MUTED,
    VALUE_STYLE,
)


def section_card(title: str, icon: str | None = None):
    """Context manager: a styled card with a section title header.

    Usage::

        with section_card("Secondary Coil", "bolt"):
            ui.number(...)
    """
    card = ui.card().classes("w-full").style(CARD_STYLE)
    with card:
        with ui.row().classes("items-center gap-2 mb-4"):
            if icon:
                ui.icon(icon).classes("text-lg").style(f"color: {ACCENT};")
            ui.label(title).classes("text-lg font-semibold").style(SECTION_TITLE_STYLE)
    return card


def result_value(label_text: str, initial: str = "\u2014") -> ui.label:
    """Render a label/value pair in the standard results style.

    Returns the value label so callers can update ``label.text`` reactively.
    """
    with ui.column().classes("gap-0"):
        ui.label(label_text).classes("text-xs uppercase tracking-wider").style(LABEL_STYLE)
        val = ui.label(initial).classes("text-xl font-bold").style(VALUE_STYLE)
    return val


def metric_card(
    title: str,
    value: str = "\u2014",
    unit: str = "",
    border_color: str = ACCENT,
) -> tuple[ui.label, ui.label]:
    """Headline metric card with a colored top border.

    Returns ``(value_label, unit_label)`` so callers can update them.
    """
    with ui.card().classes("flex-1 min-w-[200px]").style(
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
    """A two-column grid for label/value result pairs."""
    return ui.grid(columns=2).classes("w-full gap-x-4 gap-y-3")


def result_row(grid: ui.element, name: str) -> ui.label:
    """Add a label/value row inside an existing results_grid. Returns the value label."""
    with grid:
        ui.label(name).classes("text-xs uppercase tracking-wider").style(LABEL_STYLE)
        lbl = ui.label("\u2014").classes("text-xl font-bold").style(VALUE_STYLE)
    return lbl
