from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import UnitSystem
from ui.state import AppState
from ui.theme import ACCENT, SURFACE, SURFACE_BORDER, TEXT, TEXT_DIM


def render(state: AppState) -> None:
    with ui.header(elevated=False).classes("items-center justify-between px-6").style(
        f"background: {SURFACE} !important; "
        f"border-bottom: 1px solid {SURFACE_BORDER} !important; "
        f"box-shadow: none !important;"
    ):
        with ui.row().classes("items-center gap-3"):
            # Lightning bolt icon
            ui.icon("bolt").classes("text-2xl").style(f"color: {ACCENT};")
            ui.label("PyTeslaCoil").classes("text-xl font-bold tracking-wide").style(
                f"color: {TEXT}; font-family: Inter, system-ui, sans-serif;"
            )
            ui.label("Tesla Coil Design Calculator").classes("text-sm").style(
                f"color: {TEXT_DIM};"
            )

        with ui.row().classes("items-center gap-3"):
            unit_select = ui.select(
                {UnitSystem.INCHES: "inches", UnitSystem.CM: "cm"},
                value=state.design.unit_system,
                label="Units",
            ).classes("w-28").style(f"color: {TEXT};")

            def _on_units_change(e):
                state.design.unit_system = e.value
                state.recalculate()

            unit_select.on_value_change(_on_units_change)

            ui.button(
                "Load Demo", icon="science", on_click=lambda: _open_presets(state)
            ).style(
                f"background: transparent; border: 1px solid {ACCENT}; "
                f"color: {ACCENT}; border-radius: 6px;"
            )


def _open_presets(state: AppState) -> None:
    from ui.components.presets_dialog import show_presets
    show_presets(state)
