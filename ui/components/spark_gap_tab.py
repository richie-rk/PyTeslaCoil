from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.spark_gap_model import RotaryGapInput, StaticGapInput
from pyteslacoil.units import inches_to_meters, length_in, length_to_meters, nf_to_farads
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState
from ui.theme import SURFACE_BORDER


def _default_static(state: AppState) -> StaticGapInput:
    cap = (
        state.design.primary.capacitance
        if state.design.primary
        else nf_to_farads(10.0)
    )
    v_peak = (
        state.outputs.transformer.output_voltage_peak
        if state.outputs.transformer
        else 12_000.0 * 1.414
    )
    return StaticGapInput(
        num_electrodes=4,
        electrode_diameter=inches_to_meters(0.5),
        total_gap_spacing=inches_to_meters(0.15),
        transformer_voltage_peak=v_peak,
        tank_capacitance=cap,
    )


def _default_rotary(state: AppState) -> RotaryGapInput:
    cap = (
        state.design.primary.capacitance
        if state.design.primary
        else nf_to_farads(10.0)
    )
    v_peak = (
        state.outputs.transformer.output_voltage_peak
        if state.outputs.transformer
        else 15_000.0 * 1.414
    )
    return RotaryGapInput(
        num_stationary_electrodes=2,
        num_rotating_electrodes=8,
        disc_rpm=3000.0,
        rotating_electrode_diameter=inches_to_meters(0.25),
        stationary_electrode_diameter=inches_to_meters(0.25),
        rotating_path_diameter=inches_to_meters(8.0),
        transformer_voltage_peak=v_peak,
        tank_capacitance=cap,
    )


def render(state: AppState) -> None:
    if state.design.static_gap is None:
        state.design.static_gap = _default_static(state)
    if state.design.rotary_gap is None:
        state.design.rotary_gap = _default_rotary(state)

    unit = state.design.unit_system.value

    with ui.tabs().classes("w-full").style(
        f"background: transparent; border-bottom: 1px solid {SURFACE_BORDER};"
    ) as gap_tabs:
        static = ui.tab("Static")
        rotary = ui.tab("Rotary")

    with ui.tab_panels(gap_tabs, value=static).classes("w-full"):
        with ui.tab_panel(static):
            _render_static(state, unit)
        with ui.tab_panel(rotary):
            _render_rotary(state, unit)


def _render_static(state: AppState, unit: str) -> None:
    sg = state.design.static_gap
    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Static Gap", "flash_on"):
                n = ui.number(
                    label="# electrodes",
                    value=sg.num_electrodes,
                    min=2,
                    step=1,
                    format="%.0f",
                ).classes("w-full")
                d = ui.number(
                    label=f"Electrode diameter ({unit})",
                    value=length_in(sg.electrode_diameter, unit),
                    step=0.05,
                    format="%.3f",
                ).classes("w-full")
                gap = ui.number(
                    label=f"Total gap spacing ({unit})",
                    value=length_in(sg.total_gap_spacing, unit),
                    step=0.01,
                    format="%.4f",
                ).classes("w-full")
                vpk = ui.number(
                    label="Transformer V_peak (V)",
                    value=sg.transformer_voltage_peak,
                    step=100,
                    format="%.0f",
                ).classes("w-full")
                cap = ui.number(
                    label="Tank capacitance (nF)",
                    value=sg.tank_capacitance * 1e9,
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")
                fline = ui.number(
                    label="Line frequency (Hz)",
                    value=sg.line_frequency_hz,
                    step=10,
                    format="%.0f",
                ).classes("w-full")

                def _apply():
                    try:
                        new = StaticGapInput(
                            num_electrodes=int(n.value),
                            electrode_diameter=length_to_meters(d.value, unit),
                            total_gap_spacing=length_to_meters(gap.value, unit),
                            transformer_voltage_peak=float(vpk.value),
                            tank_capacitance=float(cap.value) * 1e-9,
                            line_frequency_hz=float(fline.value),
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.static_gap = new
                    state.recalculate()

                for w in (n, d, gap, vpk, cap, fline):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)

        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Results", "assessment"):
                grid = results_grid()
                lbl_gap = result_row(grid, "Gap per electrode")
                lbl_vbk = result_row(grid, "Breakdown voltage")
                lbl_pct = result_row(grid, "% cap charged")
                lbl_bps = result_row(grid, "BPS")
                lbl_e = result_row(grid, "Energy / bang")
                lbl_spark = result_row(grid, "Spark length")

            def _refresh(_state: AppState):
                out = _state.outputs.static_gap
                if out is None:
                    return
                lbl_gap.text = f"{out.gap_per_electrode_m * 1000:.2f} mm"
                lbl_vbk.text = f"{out.breakdown_voltage_v / 1000:.2f} kV"
                lbl_pct.text = f"{out.percent_cap_charged:.1f} %"
                lbl_bps.text = f"{out.bps:.0f}"
                lbl_e.text = f"{out.effective_cap_energy_j:.3f} J"
                lbl_spark.text = (
                    f"{out.spark_length_m * 100:.1f} cm  "
                    f"({out.spark_length_m / 0.0254:.1f} in)"
                )

            state.subscribe(_refresh)


def _render_rotary(state: AppState, unit: str) -> None:
    rg = state.design.rotary_gap
    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Rotary Gap", "settings"):
                ns = ui.number(
                    label="# stationary electrodes",
                    value=rg.num_stationary_electrodes,
                    min=1,
                    step=1,
                    format="%.0f",
                ).classes("w-full")
                nr = ui.number(
                    label="# rotating electrodes",
                    value=rg.num_rotating_electrodes,
                    min=1,
                    step=1,
                    format="%.0f",
                ).classes("w-full")
                rpm = ui.number(
                    label="Disc RPM",
                    value=rg.disc_rpm,
                    step=100,
                    format="%.0f",
                ).classes("w-full")
                rd = ui.number(
                    label=f"Rotating electrode diameter ({unit})",
                    value=length_in(rg.rotating_electrode_diameter, unit),
                    step=0.05,
                    format="%.3f",
                ).classes("w-full")
                sd = ui.number(
                    label=f"Stationary electrode diameter ({unit})",
                    value=length_in(rg.stationary_electrode_diameter, unit),
                    step=0.05,
                    format="%.3f",
                ).classes("w-full")
                pdia = ui.number(
                    label=f"Rotating path diameter ({unit})",
                    value=length_in(rg.rotating_path_diameter, unit),
                    step=0.5,
                    format="%.3f",
                ).classes("w-full")
                vpk = ui.number(
                    label="Transformer V_peak (V)",
                    value=rg.transformer_voltage_peak,
                    step=100,
                    format="%.0f",
                ).classes("w-full")
                cap = ui.number(
                    label="Tank capacitance (nF)",
                    value=rg.tank_capacitance * 1e9,
                    step=0.1,
                    format="%.3f",
                ).classes("w-full")

                def _apply():
                    try:
                        new = RotaryGapInput(
                            num_stationary_electrodes=int(ns.value),
                            num_rotating_electrodes=int(nr.value),
                            disc_rpm=float(rpm.value),
                            rotating_electrode_diameter=length_to_meters(rd.value, unit),
                            stationary_electrode_diameter=length_to_meters(sd.value, unit),
                            rotating_path_diameter=length_to_meters(pdia.value, unit),
                            transformer_voltage_peak=float(vpk.value),
                            tank_capacitance=float(cap.value) * 1e-9,
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.rotary_gap = new
                    state.recalculate()

                for w in (ns, nr, rpm, rd, sd, pdia, vpk, cap):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)

        with ui.column().classes("flex-1 min-w-[300px]"):
            with section_card("Results", "assessment"):
                grid = results_grid()
                lbl_ppr = result_row(grid, "Presentations / rev")
                lbl_bps = result_row(grid, "BPS")
                lbl_tip = result_row(grid, "Tip speed")
                lbl_fr = result_row(grid, "Firing rate")
                lbl_pct = result_row(grid, "% cap charged")
                lbl_e = result_row(grid, "Energy / bang")
                lbl_spark = result_row(grid, "Spark length")

            def _refresh(_state: AppState):
                out = _state.outputs.rotary_gap
                if out is None:
                    return
                lbl_ppr.text = f"{out.presentations_per_revolution}"
                lbl_bps.text = f"{out.bps:.0f}"
                lbl_tip.text = f"{out.rotational_speed_m_per_s:.1f} m/s"
                lbl_fr.text = f"{out.firing_rate_s * 1e6:.2f} \u00b5s"
                lbl_pct.text = f"{out.percent_cap_charged:.1f} %"
                lbl_e.text = f"{out.effective_cap_energy_j:.3f} J"
                lbl_spark.text = (
                    f"{out.spark_length_m * 100:.1f} cm  "
                    f"({out.spark_length_m / 0.0254:.1f} in)"
                )

            state.subscribe(_refresh)
