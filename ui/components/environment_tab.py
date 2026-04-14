from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.environment_model import EnvironmentInput
from pyteslacoil.units import length_in, length_to_meters
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState


def render(state: AppState) -> None:
    if state.design.environment is None:
        state.design.environment = EnvironmentInput()
    env = state.design.environment
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        # ── Inputs ─────────────────────────────────────────────────
        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Surrounding Environment", "public"):
                gp = ui.number(
                    label=f"Ground plane radius ({unit}, 0 = none)",
                    value=length_in(env.ground_plane_radius, unit),
                    step=1,
                    format="%.2f",
                ).classes("w-full")
                wr = ui.number(
                    label=f"Wall radius ({unit}, 0 = none)",
                    value=length_in(env.wall_radius, unit),
                    step=1,
                    format="%.2f",
                ).classes("w-full")
                ch = ui.number(
                    label=f"Ceiling height ({unit}, 0 = none)",
                    value=length_in(env.ceiling_height, unit),
                    step=1,
                    format="%.2f",
                ).classes("w-full")

                def _apply():
                    try:
                        new = EnvironmentInput(
                            ground_plane_radius=length_to_meters(gp.value, unit),
                            wall_radius=length_to_meters(wr.value, unit),
                            ceiling_height=length_to_meters(ch.value, unit),
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.environment = new
                    state.recalculate()

                for w in (gp, wr, ch):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)

        # ── Results ────────────────────────────────────────────────
        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Computed Factors", "calculate"):
                grid = results_grid()
                lbl_f = result_row(grid, "Proximity correction")
                lbl_n = result_row(grid, "Notes")

            def _refresh(_state: AppState):
                out = _state.outputs.environment
                if out is None:
                    return
                lbl_f.text = f"{out.proximity_correction_factor:.3f}"
                lbl_n.text = out.notes

            state.subscribe(_refresh)
            state.recalculate()
