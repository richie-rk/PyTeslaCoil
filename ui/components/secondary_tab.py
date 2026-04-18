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
)
from pyteslacoil.wire_data import AVAILABLE_AWG
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState


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

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        # ── Inputs ─────────────────────────────────────────────────
        with ui.column().classes("flex-[6] sm:min-w-[300px]"):
            with section_card("Secondary Coil Design", "bolt"):
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    with ui.column().classes("flex-1 min-w-[180px] gap-3"):
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

                    with ui.column().classes("flex-1 min-w-[180px] gap-3"):
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
                            label="Temperature (\u00b0C)",
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

        # ── Results ────────────────────────────────────────────────
        with ui.column().classes("flex-[4] sm:min-w-[300px]"):
            with section_card("Results", "assessment"):
                grid = results_grid()
                lbl_L = result_row(grid, "Inductance")
                lbl_C = result_row(grid, "Self-capacitance")
                lbl_f = result_row(grid, "Resonant freq (bare)")
                lbl_fsys = result_row(grid, "Resonant freq (with topload)")
                lbl_wire = result_row(grid, "Wire length")
                lbl_rdc = result_row(grid, "DC resistance")
                lbl_rac = result_row(grid, "AC resistance")
                lbl_Q = result_row(grid, "Q factor")
                lbl_Z = result_row(grid, "Impedance")
                lbl_ar = result_row(grid, "Aspect ratio")
                lbl_geom = result_row(grid, "Geometry")

            def _refresh(_state: AppState) -> None:
                out = _state.outputs.secondary
                if out is None:
                    return
                lbl_L.text = f"{out.inductance_mh:.3f} mH"
                lbl_C.text = f"{out.self_capacitance_pf:.2f} pF"
                lbl_f.text = f"{out.resonant_frequency_khz:.2f} kHz"
                if out.system_resonant_frequency_khz:
                    lbl_fsys.text = f"{out.system_resonant_frequency_khz:.2f} kHz"
                else:
                    lbl_fsys.text = "\u2014"
                lbl_wire.text = f"{out.wire_length_m:.1f} m  ({out.wire_length_ft:.1f} ft)"
                lbl_rdc.text = f"{out.dc_resistance_ohms:.2f} \u03a9"
                lbl_rac.text = f"{out.ac_resistance_ohms:.2f} \u03a9"
                lbl_Q.text = f"{out.q_factor:.0f}"
                lbl_Z.text = f"{out.impedance_ohms:,.0f} \u03a9"
                lbl_ar.text = f"{out.aspect_ratio:.2f}"
                lbl_geom.text = out.coil_geometry.value

            state.subscribe(_refresh)
            state.recalculate()
