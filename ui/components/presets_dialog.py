from __future__ import annotations

from nicegui import ui

from pyteslacoil.presets import AVAILABLE_PRESETS, load_preset
from ui.state import AppState


def show_presets(state: AppState) -> None:
    with ui.dialog() as dialog, ui.card().classes("p-4 min-w-[350px]"):
        ui.label("Load a demo coil").classes("text-lg font-semibold mb-2")
        for preset_id, label in AVAILABLE_PRESETS.items():
            def _load(p=preset_id):
                state.design = load_preset(p)
                state.recalculate()
                dialog.close()
                ui.notify(f"Loaded preset: {AVAILABLE_PRESETS[p]}", type="positive")

            ui.button(label, on_click=_load).classes("w-full mb-2").props(
                "color=cyan flat"
            )
        ui.button("Cancel", on_click=dialog.close).props("flat")
    dialog.open()
