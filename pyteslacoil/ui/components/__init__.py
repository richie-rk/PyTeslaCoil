"""NiceGUI component modules.

Each ``*_tab`` module exports a ``render(state)`` function that builds a tab
panel bound to the per-browser-tab :class:`~pyteslacoil.ui.state.AppState`.
"""

from pyteslacoil.ui.components import (
    cards,
    coil_visualizer,
    coupling_tab,
    environment_tab,
    header,
    inputs,
    presets_dialog,
    primary_tab,
    results_tab,
    secondary_tab,
    spark_gap_tab,
    topload_tab,
    transformer_tab,
)

__all__ = [
    "cards",
    "inputs",
    "header",
    "secondary_tab",
    "primary_tab",
    "topload_tab",
    "coupling_tab",
    "spark_gap_tab",
    "transformer_tab",
    "environment_tab",
    "results_tab",
    "coil_visualizer",
    "presets_dialog",
]
