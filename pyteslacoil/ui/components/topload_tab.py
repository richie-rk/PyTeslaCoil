"""Topload tab: toroid / sphere geometry and its capacitance."""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.models import ToploadInput, ToploadType
from pyteslacoil.ui.components.cards import clear_rows, fmt, result_rows, results_grid, section_card
from pyteslacoil.ui.components.inputs import ErrorLabel, length_input, meters, on_change
from pyteslacoil.ui.defaults import default_topload
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import TAB_ROW_CLASS

TYPES = {ToploadType.TOROID: "Toroid", ToploadType.SPHERE: "Sphere", ToploadType.NONE: "None"}


def _inputs(state: AppState) -> None:
    top = state.design.topload or ToploadInput(topload_type=ToploadType.NONE)
    shown = default_topload()  # dimensions to show for fields the design does not set
    unit = state.design.unit_system.value

    kind = ui.select(TYPES, value=top.topload_type, label="Type").classes("w-full")
    major = length_input(
        "Major (outer) diameter", top.major_diameter or shown.major_diameter or 0.0, unit, step=0.5
    )
    minor = length_input(
        "Minor (tube) diameter", top.minor_diameter or shown.minor_diameter or 0.0, unit, step=0.1
    )
    for widget in (major, minor):
        widget.bind_visibility_from(kind, "value", backward=lambda v: v == ToploadType.TOROID)
    sphere = length_input(
        "Sphere diameter", top.sphere_diameter or shown.major_diameter or 0.0, unit, step=0.5
    )
    sphere.bind_visibility_from(kind, "value", backward=lambda v: v == ToploadType.SPHERE)
    height = length_input(
        "Height of the centre above ground", top.height or shown.height or 0.0, unit, step=0.5
    )
    height.bind_visibility_from(kind, "value", backward=lambda v: v != ToploadType.NONE)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            if kind.value == ToploadType.TOROID:
                new = ToploadInput(
                    topload_type=ToploadType.TOROID,
                    major_diameter=meters(major, unit),
                    minor_diameter=meters(minor, unit),
                    height=meters(height, unit),
                )
            elif kind.value == ToploadType.SPHERE:
                new = ToploadInput(
                    topload_type=ToploadType.SPHERE,
                    sphere_diameter=meters(sphere, unit),
                    height=meters(height, unit),
                )
            else:
                new = ToploadInput(topload_type=ToploadType.NONE)
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("topload", new)

    on_change((kind, major, minor, sphere, height), apply)


def render(state: AppState) -> None:
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Topload Geometry", "circle"):
                inputs = ui.refreshable(_inputs)
                inputs(state)

        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Results", "assessment"):
                rows = result_rows(
                    results_grid(),
                    {
                        "c": "Capacitance (free space)",
                        "c_eff": "Capacitance (with environment)",
                        "fsys": "System f (with secondary)",
                        "type": "Type",
                    },
                )

    def refresh(s: AppState) -> None:
        out = s.outputs.topload
        if out is None:
            clear_rows(rows)
            return
        rows["c"].text = f"{out.capacitance_pf:.2f} pF"
        rows["c_eff"].text = fmt(s.outputs.effective_topload_capacitance_pf, ".2f", "pF")
        rows["fsys"].text = fmt(s.outputs.system_resonant_frequency_khz, ".2f", "kHz")
        rows["type"].text = out.topload_type.value

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
