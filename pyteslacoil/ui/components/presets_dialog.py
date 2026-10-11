"""Dialog for loading one of the demo coil presets."""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.presets import AVAILABLE_PRESETS, load_preset
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import (
    ACCENT,
    SURFACE,
    SURFACE_BORDER,
    SURFACE_ELEVATED,
    TEXT,
    TEXT_DIM,
)


def show_presets(state: AppState) -> None:
    with ui.dialog() as dialog, ui.card().style(
        f"background: {SURFACE_ELEVATED}; border: 1px solid {SURFACE_BORDER}; "
        f"border-radius: 8px; padding: 24px; min-width: min(400px, 90vw);"
    ):
        ui.label("Load a Demo Coil").classes("text-lg font-semibold mb-4").style(f"color: {TEXT};")

        for preset_id, label in AVAILABLE_PRESETS.items():

            def _load(p: str = preset_id) -> None:
                state.replace_design(load_preset(p))
                dialog.close()
                ui.notify(f"Loaded preset: {AVAILABLE_PRESETS[p]}", type="positive")

            with ui.card().classes("w-full cursor-pointer").style(
                f"background: {SURFACE}; border: 1px solid {SURFACE_BORDER}; "
                f"border-radius: 8px; padding: 16px; margin-bottom: 8px; "
                f"transition: border-color 0.2s;"
            ).mark(f"preset-{preset_id}").on("click", _load):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("bolt").style(f"color: {ACCENT}; font-size: 20px;")
                    with ui.column().classes("gap-0"):
                        ui.label(label).classes("font-semibold").style(f"color: {TEXT};")
                        ui.label(f"Preset: {preset_id}").classes("text-xs").style(
                            f"color: {TEXT_DIM};"
                        )

        ui.button("Cancel", on_click=dialog.close).style(
            f"color: {TEXT_DIM}; margin-top: 8px;"
        ).props("flat")

    dialog.open()
