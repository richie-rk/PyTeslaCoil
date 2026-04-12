"""Secondary coil tab.

The user enters geometry in their preferred unit system and the tab shows
live computed outputs (inductance, self-capacitance, frequency, Q, etc.).
"""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.units import (
    inches_to_meters,
    length_in,
    length_to_meters,
    meters_to_inches,
)
from pyteslacoil.wire_data import AVAILABLE_AWG
from ui.state import AppState
from ui.theme import CARD_CLASS, LABEL_CLASS, SECTION_TITLE_CLASS, VALUE_CLASS

# A reasonable default secondary so the tab boots with usable values.
def _default_secondary() -> SecondaryInput:
    return SecondaryInput(
        radius_1=inches_to_meters(2.125),
        radius_2=inches_to_meters(2.125),
        height_1=inches_to_meters(3.0),
        height_2=inches_to_meters(19.0),
        turns=711,
        wire_awg=24,
    )


def render(state: AppState) -> None:
    """Build the Secondary tab."""
    if state.design.secondary is None:
        state.design.secondary = _default_secondary()

    sec = state.design.secondary
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-6"):
        # ----- inputs ---------------------------------------------------
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Geometry").classes(SECTION_TITLE_CLASS)

                diam_in = ui.number(
                    label=f"Coil diameter ({unit})",
                    value=length_in(2 * sec.radius_1, unit),
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")

                h1 = ui.number(
                    label=f"Winding start height ({unit})",
                    value=length_in(sec.height_1, unit),
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")
                h2 = ui.number(
                    label=f"Winding end height ({unit})",
                    value=length_in(sec.height_2, unit),
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")
                turns = ui.number(
                    label="Number of turns",
                    value=float(sec.turns),
                    min=1,
                    step=1,
                    format="%.0f",
                ).classes("w-full")
                awg = ui.select(
                    {a: f"AWG {a}" for a in AVAILABLE_AWG},
                    value=sec.wire_awg,
                    label="Wire gauge",
                ).classes("w-full")
                temp = ui.number(
                    label="Temperature (°C)",
                    value=sec.temperature_c,
                    step=1,
                    format="%.1f",
                ).classes("w-full")

                def _apply():
                    try:
                        new = SecondaryInput(
                            radius_1=length_to_meters(diam_in.value / 2.0, unit),
                            radius_2=length_to_meters(diam_in.value / 2.0, unit),
                            height_1=length_to_meters(h1.value, unit),
                            height_2=length_to_meters(h2.value, unit),
                            turns=int(turns.value),
                            wire_awg=int(awg.value),
                            temperature_c=float(temp.value),
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.secondary = new
                    state.recalculate()

                for w in (diam_in, h1, h2, turns, temp):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)
                awg.on_value_change(lambda *_: _apply())

        # ----- outputs --------------------------------------------------
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Results").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                def _row(name: str, key: str) -> None:
                    with grid:
                        ui.label(name).classes(LABEL_CLASS)
                        labels[key] = ui.label("—").classes(VALUE_CLASS)

                _row("Inductance", "L")
                _row("Self-capacitance", "C")
                _row("Resonant freq (bare)", "f")
                _row("Resonant freq (with topload)", "f_sys")
                _row("Wire length", "wire")
                _row("DC resistance", "rdc")
                _row("AC resistance", "rac")
                _row("Q factor", "Q")
                _row("Impedance", "Z")
                _row("Aspect ratio", "ar")
                _row("Geometry", "geom")

            def _refresh(_state: AppState) -> None:
                out = _state.outputs.secondary
                if out is None:
                    return
                labels["L"].text = f"{out.inductance_mh:.3f} mH"
                labels["C"].text = f"{out.self_capacitance_pf:.2f} pF"
                labels["f"].text = f"{out.resonant_frequency_khz:.2f} kHz"
                if out.system_resonant_frequency_khz:
                    labels["f_sys"].text = (
                        f"{out.system_resonant_frequency_khz:.2f} kHz"
                    )
                else:
                    labels["f_sys"].text = "—"
                labels["wire"].text = (
                    f"{out.wire_length_m:.1f} m  ({out.wire_length_ft:.1f} ft)"
                )
                labels["rdc"].text = f"{out.dc_resistance_ohms:.2f} Ω"
                labels["rac"].text = f"{out.ac_resistance_ohms:.2f} Ω"
                labels["Q"].text = f"{out.q_factor:.0f}"
                labels["Z"].text = f"{out.impedance_ohms:,.0f} Ω"
                labels["ar"].text = f"{out.aspect_ratio:.2f}"
                labels["geom"].text = out.coil_geometry.value

            state.subscribe(_refresh)
            state.recalculate()
