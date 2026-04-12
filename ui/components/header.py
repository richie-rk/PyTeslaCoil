from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import UnitSystem
from ui.state import AppState
from ui.theme import PRIMARY, TEXT


def render(state: AppState) -> None:
    with ui.header(elevated=True).classes(
        "items-center justify-between bg-slate-900 text-cyan-200"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.html(
                '<span style="font-size:1.6rem">⚡</span>'
            )
            ui.label("PyTeslaCoil").classes("text-2xl font-bold tracking-wide")
            ui.label("· Tesla coil design calculator").classes(
                "text-sm text-slate-400"
            )

        with ui.row().classes("items-center gap-3"):
            unit_select = ui.select(
                {UnitSystem.INCHES: "inches", UnitSystem.CM: "cm"},
                value=state.design.unit_system,
                label="Units",
            ).classes("w-32")

            def _on_units_change(e):
                state.design.unit_system = e.value
                state.recalculate()

            unit_select.on_value_change(_on_units_change)

            ui.button(
                "Load Demo", on_click=lambda: _open_presets(state)
            ).props("flat color=cyan")
            ui.button(
                "Recalculate", on_click=state.recalculate
            ).props("color=primary")


def _open_presets(state: AppState) -> None:
    from ui.components.presets_dialog import show_presets

    show_presets(state)
