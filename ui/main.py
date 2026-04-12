"""NiceGUI entry point for PyTeslaCoil.

Run with ``python -m ui.main`` or use the ``pyteslacoil`` console script
that ``pyproject.toml`` installs.
"""

from __future__ import annotations

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


def build_ui() -> AppState:
    state = AppState()

    header.render(state)

    with ui.column().classes("w-full p-6"):
        with ui.tabs().classes("w-full") as tabs:
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
        port=8080,
        reload=False,
        dark=True,
        favicon="⚡",
    )


# NiceGUI's auto-reload mechanism imports the module twice — once as
# ``__main__`` and once as ``__mp_main__``. The dual condition guards
# against double-instantiation while still allowing both modes to work.
if __name__ in {"__main__", "__mp_main__"}:
    run()
