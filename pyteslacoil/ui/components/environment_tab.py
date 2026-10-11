"""Environment tab: grounded surfaces near the topload."""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.models import EnvironmentInput
from pyteslacoil.ui.components.cards import clear_rows, fmt, result_rows, results_grid, section_card
from pyteslacoil.ui.components.inputs import ErrorLabel, length_input, meters, on_change
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import TAB_ROW_CLASS, TEXT_DIM


def _inputs(state: AppState) -> None:
    env = state.design.environment or EnvironmentInput()
    unit = state.design.unit_system.value

    ui.label(
        "Grounded surfaces raise the topload capacitance. Enter 0 for a surface that is not present."
    ).classes("text-sm").style(f"color: {TEXT_DIM};")
    ground = length_input("Ground plane radius", env.ground_plane_radius, unit, step=1, decimals=2)
    walls = length_input("Distance from the coil axis to the walls", env.wall_radius, unit, step=1, decimals=2)
    ceiling = length_input("Ceiling height above the ground plane", env.ceiling_height, unit, step=1, decimals=2)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            new = EnvironmentInput(
                ground_plane_radius=meters(ground, unit),
                wall_radius=meters(walls, unit),
                ceiling_height=meters(ceiling, unit),
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("environment", new)

    on_change((ground, walls, ceiling), apply)


def render(state: AppState) -> None:
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Surrounding Environment", "public"):
                inputs = ui.refreshable(_inputs)
                inputs(state)

        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Computed Factors", "calculate"):
                rows = result_rows(
                    results_grid(),
                    {
                        "f": "Proximity correction",
                        "c": "Topload capacitance (corrected)",
                        "n": "Notes",
                    },
                )

    def refresh(s: AppState) -> None:
        out = s.outputs.environment
        if out is None:
            clear_rows(rows)
            return
        rows["f"].text = f"{out.proximity_correction_factor:.3f}"
        rows["c"].text = fmt(s.outputs.effective_topload_capacitance_pf, ".2f", "pF")
        rows["n"].text = out.notes

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
