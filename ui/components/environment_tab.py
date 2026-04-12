from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.environment_model import EnvironmentInput
from pyteslacoil.units import length_in, length_to_meters
from ui.state import AppState
from ui.theme import CARD_CLASS, LABEL_CLASS, SECTION_TITLE_CLASS, VALUE_CLASS


def render(state: AppState) -> None:
    if state.design.environment is None:
        state.design.environment = EnvironmentInput()
    env = state.design.environment
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Surrounding environment").classes(SECTION_TITLE_CLASS)
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

        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Computed factors").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                with grid:
                    ui.label("Proximity correction").classes(LABEL_CLASS)
                    labels["f"] = ui.label("—").classes(VALUE_CLASS)
                    ui.label("Notes").classes(LABEL_CLASS)
                    labels["n"] = ui.label("—").classes(VALUE_CLASS)

            def _refresh(_state: AppState):
                out = _state.outputs.environment
                if out is None:
                    return
                labels["f"].text = f"{out.proximity_correction_factor:.3f}"
                labels["n"].text = out.notes

            state.subscribe(_refresh)
            state.recalculate()
