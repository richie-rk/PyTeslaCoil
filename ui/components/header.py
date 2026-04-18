from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import UnitSystem
from ui.state import AppState
from ui.theme import ACCENT, SURFACE, SURFACE_BORDER, TEXT, TEXT_DIM


def render(state: AppState) -> None:
    with ui.header(elevated=False).classes(
        "items-center justify-between px-3 sm:px-6 gap-2 flex-wrap"
    ).style(
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
            ui.label("Tesla Coil Design Calculator").classes(
                "text-sm hidden md:block"
            ).style(f"color: {TEXT_DIM};")

        # Center section — GitHub logo
        with ui.link(
            target="https://github.com/richie-rk/PyTeslaCoil", new_tab=True
        ).classes("no-underline"):
            ui.html(
                f'<svg viewBox="0 0 24 24" width="32" height="32"'
                f' fill="{TEXT_DIM}" class="github-icon" style="cursor:pointer;">'
                '<path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 '
                "11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555"
                "-3.795-.735-3.795-.735-.54-1.38-1.32-1.74-1.32-1.74-1.08-.735.075"
                "-.72.075-.72 1.2.084 1.83 1.23 1.83 1.23 1.065 1.815 2.79 1.29 "
                "3.465.99.105-.765.42-1.29.765-1.59-2.415-.27-4.965-1.2-4.965"
                "-5.385 0-1.185.42-2.16 1.11-2.925-.105-.27-.48-1.38.105-2.88 0 0 "
                ".915-.3 2.985 1.11a10.3 10.3 0 0 1 2.73-.375c.93.015 1.86.135 "
                "2.73.375 2.07-1.41 2.985-1.11 2.985-1.11.585 1.5.21 2.61.105 "
                "2.88.69.765 1.11 1.74 1.11 2.925 0 4.2-2.555 5.115-4.98 5.385.39"
                ".33.75 1.005.75 2.025 0 1.47-.015 2.655-.015 3.015 0 .315.225.69"
                '.84.57C20.565 21.795 24 17.31 24 12c0-6.63-5.37-12-12-12z"/>'
                "</svg>"
                f"<style>.github-icon:hover {{ fill: {ACCENT} !important; }}</style>"
            ).tooltip("View on GitHub")

        # Right section
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
