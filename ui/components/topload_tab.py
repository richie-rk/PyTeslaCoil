from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import ToploadType
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.units import inches_to_meters, length_in, length_to_meters
from ui.state import AppState
from ui.theme import CARD_CLASS, LABEL_CLASS, SECTION_TITLE_CLASS, VALUE_CLASS


def _default_topload() -> ToploadInput:
    return ToploadInput(
        topload_type=ToploadType.TOROID,
        major_diameter=inches_to_meters(6.0),
        minor_diameter=inches_to_meters(1.5),
        height=inches_to_meters(20.0),
    )


def render(state: AppState) -> None:
    if state.design.topload is None:
        state.design.topload = _default_topload()
    top = state.design.topload
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Topload geometry").classes(SECTION_TITLE_CLASS)

                type_select = ui.select(
                    {ToploadType.TOROID: "Toroid", ToploadType.SPHERE: "Sphere", ToploadType.NONE: "None"},
                    value=top.topload_type,
                    label="Type",
                ).classes("w-full")

                major = ui.number(
                    label=f"Major (outer) diameter ({unit})",
                    value=length_in(top.major_diameter or 0.0, unit),
                    step=0.5,
                    format="%.3f",
                ).classes("w-full")
                minor = ui.number(
                    label=f"Minor (tube) diameter ({unit})",
                    value=length_in(top.minor_diameter or 0.0, unit),
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")
                sphere = ui.number(
                    label=f"Sphere diameter ({unit})",
                    value=length_in(top.sphere_diameter or 0.0, unit),
                    step=0.5,
                    format="%.3f",
                ).classes("w-full")
                height = ui.number(
                    label=f"Height above ground ({unit})",
                    value=length_in(top.height, unit),
                    step=0.5,
                    format="%.3f",
                ).classes("w-full")

                def _apply():
                    t = type_select.value
                    try:
                        if t == ToploadType.TOROID:
                            new = ToploadInput(
                                topload_type=ToploadType.TOROID,
                                major_diameter=length_to_meters(major.value, unit),
                                minor_diameter=length_to_meters(minor.value, unit),
                                height=length_to_meters(height.value, unit),
                            )
                        elif t == ToploadType.SPHERE:
                            new = ToploadInput(
                                topload_type=ToploadType.SPHERE,
                                sphere_diameter=length_to_meters(sphere.value, unit),
                                height=length_to_meters(height.value, unit),
                            )
                        else:
                            new = ToploadInput(
                                topload_type=ToploadType.NONE,
                                height=max(length_to_meters(height.value, unit), 1e-3),
                            )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.topload = new
                    state.recalculate()

                for w in (major, minor, sphere, height):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)
                type_select.on_value_change(lambda *_: _apply())

        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Results").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                def _row(name, key):
                    with grid:
                        ui.label(name).classes(LABEL_CLASS)
                        labels[key] = ui.label("—").classes(VALUE_CLASS)

                _row("Capacitance", "C")
                _row("System f (with sec.)", "fsys")
                _row("Type", "type")

            def _refresh(_state: AppState):
                out = _state.outputs.topload
                if out is None:
                    return
                labels["C"].text = f"{out.capacitance_pf:.2f} pF"
                labels["type"].text = out.topload_type.value
                if _state.outputs.system_resonant_frequency_khz:
                    labels["fsys"].text = (
                        f"{_state.outputs.system_resonant_frequency_khz:.2f} kHz"
                    )

            state.subscribe(_refresh)
            state.recalculate()
