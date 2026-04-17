"""NiceGUI entry point for PyTeslaCoil.

Run with ``python -m ui.main`` or use the ``pyteslacoil`` console script
that ``pyproject.toml`` installs.
"""

from __future__ import annotations

import os

from nicegui import ui

from ui.components import (
    coupling_tab,
    environment_tab,
    header,
    primary_tab,
    results_tab,
    secondary_tab,
    spark_gap_tab,
    topload_tab,
    transformer_tab,
)
from ui.state import AppState
from ui.theme import GLOBAL_CSS, SURFACE_BORDER


def build_ui() -> AppState:
    state = AppState()

    # Inject global design-system CSS.
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    header.render(state)

    # Centered max-width container.
    with ui.column().classes("w-full max-w-6xl mx-auto px-6 py-4"):
        with ui.tabs().classes("w-full").style(
            f"background: transparent; border-bottom: 1px solid {SURFACE_BORDER};"
        ) as tabs:
            sec = ui.tab("Secondary", icon="bolt")
            pri = ui.tab("Primary", icon="track_changes")
            top = ui.tab("Topload", icon="circle")
            cpl = ui.tab("Coupling", icon="link")
            sg = ui.tab("Spark Gap", icon="flash_on")
            xfm = ui.tab("Transformer", icon="electric_bolt")
            env = ui.tab("Environment", icon="public")
            res = ui.tab("Results", icon="summarize")

        with ui.tab_panels(tabs, value=sec).classes("w-full"):
            with ui.tab_panel(sec):
                secondary_tab.render(state)
            with ui.tab_panel(pri):
                primary_tab.render(state)
            with ui.tab_panel(top):
                topload_tab.render(state)
            with ui.tab_panel(cpl):
                coupling_tab.render(state)
            with ui.tab_panel(sg):
                spark_gap_tab.render(state)
            with ui.tab_panel(xfm):
                transformer_tab.render(state)
            with ui.tab_panel(env):
                environment_tab.render(state)
            with ui.tab_panel(res):
                results_tab.render(state)

    return state


def run() -> None:
    build_ui()
    ui.run(
        title="PyTeslaCoil",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8080")),
        reload=False,
        show=os.environ.get("HF_SPACE") is None,
        dark=True,
        favicon="\u26a1",
    )


# NiceGUI's auto-reload mechanism imports the module twice — once as
# ``__main__`` and once as ``__mp_main__``. The dual condition guards
# against double-instantiation while still allowing both modes to work.
if __name__ in {"__main__", "__mp_main__"}:
    run()
