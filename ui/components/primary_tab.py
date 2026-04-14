from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import ConductorType
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.units import (
    farads_to_uf,
    inches_to_meters,
    length_in,
    length_to_meters,
    uf_to_farads,
)
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState


def _default_primary() -> PrimaryInput:
    return PrimaryInput(
        radius_1=inches_to_meters(3.5),
        radius_2=inches_to_meters(8.0),
        height_1=inches_to_meters(0.5),
        height_2=inches_to_meters(0.5),
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
        lead_length=inches_to_meters(30.0),
        lead_diameter=inches_to_meters(0.2),
    )


def render(state: AppState) -> None:
    if state.design.primary is None:
        state.design.primary = _default_primary()

    pri = state.design.primary
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        # ── Inputs ─────────────────────────────────────────────────
        with ui.column().classes("flex-[6] min-w-[300px]"):
            with section_card("Primary Coil Design", "track_changes"):
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1 gap-3"):
                        geom_select = ui.select(
                            ["Flat Spiral", "Helical", "Conical"],
                            value="Flat Spiral",
                            label="Primary type",
                        ).classes("w-full")
                        r1 = ui.number(
                            label=f"Inner radius ({unit})",
                            value=length_in(pri.radius_1, unit),
                            step=0.05,
                            format="%.3f",
                        ).classes("w-full")
                        r2 = ui.number(
                            label=f"Outer radius ({unit})",
                            value=length_in(pri.radius_2, unit),
                            step=0.05,
                            format="%.3f",
                        ).classes("w-full")
                        h1 = ui.number(
                            label=f"Start height ({unit})",
                            value=length_in(pri.height_1, unit),
                            step=0.05,
                            format="%.3f",
                        ).classes("w-full")
                        h2 = ui.number(
                            label=f"End height ({unit})",
                            value=length_in(pri.height_2, unit),
                            step=0.05,
                            format="%.3f",
                        ).classes("w-full")

                    with ui.column().classes("flex-1 gap-3"):
                        turns = ui.number(
                            label="Turns",
                            value=float(pri.turns),
                            min=0.1,
                            step=0.1,
                            format="%.4f",
                        ).classes("w-full")
                        wire_d = ui.number(
                            label=f"Conductor diameter ({unit})",
                            value=length_in(pri.wire_diameter, unit),
                            step=0.005,
                            format="%.4f",
                        ).classes("w-full")
                        cap = ui.number(
                            label="Tank capacitance (\u00b5F)",
                            value=farads_to_uf(pri.capacitance),
                            step=0.001,
                            format="%.4f",
                        ).classes("w-full")
                        lead_len = ui.number(
                            label=f"Lead length ({unit})",
                            value=length_in(pri.lead_length, unit),
                            step=1.0,
                            format="%.2f",
                        ).classes("w-full")
                        lead_d = ui.number(
                            label=f"Lead diameter ({unit})",
                            value=length_in(pri.lead_diameter, unit),
                            step=0.01,
                            format="%.4f",
                        ).classes("w-full")

                auto = ui.checkbox("Auto-tune turns to match secondary", value=False)
                auto.bind_value_to(state.design, "auto_tune")

                def _apply():
                    geom = geom_select.value
                    try:
                        new_r1 = length_to_meters(r1.value, unit)
                        new_r2 = length_to_meters(r2.value, unit)
                        new_h1 = length_to_meters(h1.value, unit)
                        new_h2 = length_to_meters(h2.value, unit)
                        if geom == "Flat Spiral":
                            new_h2 = new_h1
                        elif geom == "Helical":
                            new_r2 = new_r1
                        new = PrimaryInput(
                            radius_1=new_r1,
                            radius_2=new_r2,
                            height_1=new_h1,
                            height_2=new_h2,
                            turns=float(turns.value),
                            wire_diameter=length_to_meters(wire_d.value, unit),
                            capacitance=uf_to_farads(cap.value),
                            lead_length=length_to_meters(lead_len.value, unit),
                            lead_diameter=length_to_meters(lead_d.value, unit),
                            conductor_type=ConductorType.ROUND,
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.primary = new
                    state.recalculate()

                for w in (r1, r2, h1, h2, turns, wire_d, cap, lead_len, lead_d):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)
                geom_select.on_value_change(lambda *_: _apply())
                auto.on_value_change(lambda *_: state.recalculate())

        # ── Results ────────────────────────────────────────────────
        with ui.column().classes("flex-[4] min-w-[300px]"):
            with section_card("Results", "assessment"):
                grid = results_grid()
                lbl_L = result_row(grid, "Coil inductance")
                lbl_Ll = result_row(grid, "Lead inductance")
                lbl_Ltot = result_row(grid, "Total inductance")
                lbl_f = result_row(grid, "Resonant freq")
                lbl_tune = result_row(grid, "Tuning ratio")
                lbl_Z = result_row(grid, "Impedance")
                lbl_rdc = result_row(grid, "DC resistance")
                lbl_wire = result_row(grid, "Wire length")
                lbl_geom = result_row(grid, "Geometry")
                lbl_n = result_row(grid, "Turns (live)")

            def _refresh(_state: AppState) -> None:
                out = _state.outputs.primary
                if out is None:
                    return
                lbl_L.text = f"{out.inductance_uh:.2f} \u00b5H"
                lbl_Ll.text = f"{out.lead_inductance_uh:.2f} \u00b5H"
                lbl_Ltot.text = f"{out.total_inductance_uh:.2f} \u00b5H"
                lbl_f.text = f"{out.resonant_frequency_khz:.2f} kHz"
                if out.tuning_ratio:
                    lbl_tune.text = f"{out.tuning_ratio:.3f}"
                lbl_Z.text = f"{out.impedance_ohms:,.1f} \u03a9"
                lbl_rdc.text = f"{out.dc_resistance_ohms:.4f} \u03a9"
                lbl_wire.text = f"{out.wire_length_m:.2f} m  ({out.wire_length_ft:.2f} ft)"
                lbl_geom.text = out.primary_geometry.value
                if _state.design.primary:
                    lbl_n.text = f"{_state.design.primary.turns:.4f}"

            state.subscribe(_refresh)
            state.recalculate()
