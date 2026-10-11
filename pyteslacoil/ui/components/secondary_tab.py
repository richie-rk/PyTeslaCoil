"""Secondary coil tab.

The user enters geometry in their preferred unit system and the tab shows
live computed outputs (inductance, self-capacitance, frequency, Q, etc.).
"""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.models import SecondaryInput
from pyteslacoil.ui.components.cards import clear_rows, fmt, result_rows, results_grid, section_card
from pyteslacoil.ui.components.inputs import (
    ErrorLabel,
    length_input,
    meters,
    number_input,
    on_change,
    value_of,
)
from pyteslacoil.ui.defaults import default_secondary
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import (
    FIELD_COLUMN_CLASS,
    INPUT_COLUMN_CLASS,
    RESULT_COLUMN_CLASS,
    TAB_ROW_CLASS,
)
from pyteslacoil.units import length_in, length_symbol, lengths_equal
from pyteslacoil.wire_data import AVAILABLE_AWG

GEOMETRIES = {"solenoid": "Solenoid", "conical": "Conical"}


def _inputs(state: AppState) -> None:
    sec = state.design.secondary or default_secondary()
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-4 flex-wrap"):
        with ui.column().classes(FIELD_COLUMN_CLASS):
            geometry = ui.select(
                GEOMETRIES,
                value="solenoid" if lengths_equal(sec.radius_1, sec.radius_2) else "conical",
                label="Geometry",
            ).classes("w-full")
            d_bottom = length_input("Bottom diameter", 2 * sec.radius_1, unit, step=0.1)
            d_top = length_input("Top diameter", 2 * sec.radius_2, unit, step=0.1)
            d_top.bind_visibility_from(geometry, "value", backward=lambda v: v == "conical")
            h1 = length_input("Winding start height", sec.height_1, unit, step=0.1)
            h2 = length_input("Winding end height", sec.height_2, unit, step=0.1)

        with ui.column().classes(FIELD_COLUMN_CLASS):
            turns = number_input("Number of turns", sec.turns, step=1, decimals=0, minimum=1)
            awg = ui.select(
                {a: f"AWG {a}" for a in AVAILABLE_AWG}, value=sec.wire_awg, label="Wire gauge"
            ).classes("w-full")
            temp = number_input("Temperature (°C)", sec.temperature_c, step=1, decimals=1)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            r1 = meters(d_bottom, unit) / 2.0
            r2 = r1 if geometry.value == "solenoid" else meters(d_top, unit) / 2.0
            new = SecondaryInput(
                radius_1=r1,
                radius_2=r2,
                height_1=meters(h1, unit),
                height_2=meters(h2, unit),
                turns=round(value_of(turns)),
                wire_awg=int(awg.value),
                temperature_c=value_of(temp),
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("secondary", new)

    on_change((geometry, d_bottom, d_top, h1, h2, turns, awg, temp), apply)


def render(state: AppState) -> None:
    """Build the Secondary tab."""
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes(INPUT_COLUMN_CLASS):
            with section_card("Secondary Coil Design", "bolt"):
                inputs = ui.refreshable(_inputs)
                inputs(state)

        with ui.column().classes(RESULT_COLUMN_CLASS):
            with section_card("Results", "assessment"):
                rows = result_rows(
                    results_grid(),
                    {
                        "L": "Inductance",
                        "C": "Self-capacitance",
                        "f": "Resonant freq (bare)",
                        "fsys": "Resonant freq (with topload)",
                        "wire": "Wire length",
                        "pitch": "Turn pitch",
                        "rdc": "DC resistance",
                        "rac": "AC resistance (skin effect)",
                        "Q": "Q factor (bare)",
                        "Z": "Impedance",
                        "ar": "Aspect ratio (l/D)",
                        "geom": "Geometry",
                    },
                )

    def refresh(s: AppState) -> None:
        out = s.outputs.secondary
        if out is None:
            clear_rows(rows)
            return
        unit = s.design.unit_system.value
        rows["L"].text = f"{out.inductance_mh:.3f} mH"
        rows["C"].text = f"{out.self_capacitance_pf:.2f} pF"
        rows["f"].text = f"{out.resonant_frequency_khz:.2f} kHz"
        rows["fsys"].text = fmt(out.system_resonant_frequency_khz, ".2f", "kHz")
        rows["wire"].text = f"{out.wire_length_m:.1f} m  ({out.wire_length_ft:.1f} ft)"
        rows["pitch"].text = f"{length_in(out.wire_spacing_m, unit):.4f} {length_symbol(unit)}"
        rows["rdc"].text = f"{out.dc_resistance_ohms:.2f} Ω"
        rows["rac"].text = f"{out.ac_resistance_ohms:.2f} Ω"
        rows["Q"].text = f"{out.q_factor:.0f}"
        rows["Z"].text = f"{out.impedance_ohms:,.0f} Ω"
        rows["ar"].text = f"{out.aspect_ratio:.2f}"
        rows["geom"].text = out.coil_geometry.value

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
