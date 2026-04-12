"""NiceGUI component modules.

Each module exports a ``render(state)`` function that builds a tab panel
bound to the application state.
"""

from ui.components import (
    coil_visualizer,
    coupling_tab,
    environment_tab,
    header,
    presets_dialog,
    primary_tab,
    results_tab,
    secondary_tab,
    spark_gap_tab,
    topload_tab,
    transformer_tab,
)

__all__ = [
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
