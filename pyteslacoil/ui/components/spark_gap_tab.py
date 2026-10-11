"""Spark gap tab: choose the gap that drives the coil and configure it.

The charging voltage, line frequency and tank capacitance are not entered
here: they come from the Transformer and Primary tabs, so each value has a
single source of truth.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from pyteslacoil.engine.system import resolve_spark_gap_type
from pyteslacoil.models import RotaryGapInput, SparkGapType, StaticGapInput
from pyteslacoil.ui.components.cards import (
    DASH,
    clear_rows,
    fmt,
    result_rows,
    results_grid,
    section_card,
)
from pyteslacoil.ui.components.inputs import (
    ErrorLabel,
    length_input,
    meters,
    number_input,
    on_change,
    value_of,
)
from pyteslacoil.ui.defaults import default_rotary_gap, default_static_gap
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import SURFACE_BORDER, TAB_ROW_CLASS, TEXT_DIM
from pyteslacoil.units import length_in, length_symbol

GAP_TYPES = {
    SparkGapType.STATIC: "Static gap",
    SparkGapType.ROTARY: "Rotary gap",
    SparkGapType.NONE: "None (solid-state driver)",
}


def _selector(state: AppState, on_select: Callable[[SparkGapType], None]) -> None:
    select = ui.select(
        GAP_TYPES, value=resolve_spark_gap_type(state.design), label="Spark gap in use"
    ).classes("w-full")

    def apply() -> None:
        choice = SparkGapType(select.value)
        # The tabs below already show default settings for an unconfigured gap; adopt them.
        if choice == SparkGapType.STATIC and state.design.static_gap is None:
            state.design.static_gap = default_static_gap()
        if choice == SparkGapType.ROTARY and state.design.rotary_gap is None:
            state.design.rotary_gap = default_rotary_gap()
        state.set_section("spark_gap_type", choice)
        on_select(choice)

    on_change((select,), apply)


def _gap_status(state: AppState, gap: SparkGapType) -> str:
    """Why a gap's results are not driving the coil (empty if they are)."""
    configured = state.design.static_gap if gap == SparkGapType.STATIC else state.design.rotary_gap
    if configured is None:
        return "Not part of the design: choose this gap above, or edit a value, to use these settings."
    active = resolve_spark_gap_type(state.design)
    if active != gap:
        return f"Calculated for comparison; the coil is driven by: {GAP_TYPES[active]}."
    return ""


def _static_inputs(state: AppState) -> None:
    gap = state.design.static_gap or default_static_gap()
    unit = state.design.unit_system.value
    n = number_input("# electrodes", gap.num_electrodes, step=1, decimals=0, minimum=2)
    d = length_input("Electrode diameter", gap.electrode_diameter, unit, step=0.05)
    spacing = length_input("Total gap spacing", gap.total_gap_spacing, unit, step=0.01, decimals=4)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            new = StaticGapInput(
                num_electrodes=round(value_of(n)),
                electrode_diameter=meters(d, unit),
                total_gap_spacing=meters(spacing, unit),
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("static_gap", new)

    on_change((n, d, spacing), apply)


def _rotary_inputs(state: AppState) -> None:
    gap = state.design.rotary_gap or default_rotary_gap()
    unit = state.design.unit_system.value
    ns = number_input(
        "# stationary electrodes (series pairs)",
        gap.num_stationary_electrodes,
        step=1,
        decimals=0,
        minimum=1,
    )
    nr = number_input(
        "# rotating electrodes", gap.num_rotating_electrodes, step=1, decimals=0, minimum=1
    )
    rpm = number_input("Disc RPM", gap.disc_rpm, step=100, decimals=0)
    rd = length_input("Rotating electrode diameter", gap.rotating_electrode_diameter, unit, step=0.05)
    sd = length_input("Stationary electrode diameter", gap.stationary_electrode_diameter, unit, step=0.05)
    pdia = length_input("Rotating path diameter", gap.rotating_path_diameter, unit, step=0.5)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            new = RotaryGapInput(
                num_stationary_electrodes=round(value_of(ns)),
                num_rotating_electrodes=round(value_of(nr)),
                disc_rpm=value_of(rpm),
                rotating_electrode_diameter=meters(rd, unit),
                stationary_electrode_diameter=meters(sd, unit),
                rotating_path_diameter=meters(pdia, unit),
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("rotary_gap", new)

    on_change((ns, nr, rpm, rd, sd, pdia), apply)


def _tank_summary(state: AppState) -> str:
    xfmr = state.outputs.transformer
    if xfmr is None or state.design.transformer is None:
        return "No transformer is configured: enable one on the Transformer tab to charge the gap."
    pri = state.design.primary
    cap = f"{pri.capacitance * 1e9:.2f} nF" if pri else DASH
    return (
        f"Charging: {xfmr.output_voltage_peak / 1e3:.2f} kV peak at "
        f"{state.design.transformer.line_frequency_hz:.0f} Hz (Transformer tab); "
        f"tank capacitance {cap} (Primary tab)."
    )


def render(state: AppState) -> None:
    def show_gap(gap: SparkGapType) -> None:
        """Open the sub-tab of the gap that drives the coil."""
        if gap == SparkGapType.ROTARY:
            gap_tabs.set_value(rotary_tab)
        elif gap == SparkGapType.STATIC:
            gap_tabs.set_value(static_tab)

    with section_card("Spark Gap", "flash_on"):
        selector = ui.refreshable(_selector)
        selector(state, show_gap)
        tank_label = ui.label().classes("text-sm").style(f"color: {TEXT_DIM};")

    with ui.tabs().classes("w-full mt-4").style(
        f"background: transparent; border-bottom: 1px solid {SURFACE_BORDER};"
    ) as gap_tabs:
        static_tab = ui.tab("Static")
        rotary_tab = ui.tab("Rotary")

    rotary_first = resolve_spark_gap_type(state.design) == SparkGapType.ROTARY
    with ui.tab_panels(gap_tabs, value=rotary_tab if rotary_first else static_tab).classes("w-full"):
        with ui.tab_panel(static_tab):
            with ui.row().classes(TAB_ROW_CLASS):
                with ui.column().classes("flex-1 sm:min-w-[300px]"):
                    with section_card("Static Gap", "flash_on"):
                        static_inputs = ui.refreshable(_static_inputs)
                        static_inputs(state)
                with ui.column().classes("flex-1 sm:min-w-[300px]"):
                    with section_card("Results", "assessment"):
                        static_status = ui.label().classes("text-sm mb-2").style(f"color: {TEXT_DIM};")
                        static_rows = result_rows(
                            results_grid(),
                            {
                                "gap": "Gap per electrode",
                                "vbk": "Breakdown voltage",
                                "fires": "Fires",
                                "pct": "% cap charged",
                                "bps": "BPS",
                                "e": "Energy / bang",
                                "vterm": "Terminal voltage",
                                "spark": "Spark length",
                            },
                        )
        with ui.tab_panel(rotary_tab):
            with ui.row().classes(TAB_ROW_CLASS):
                with ui.column().classes("flex-1 sm:min-w-[300px]"):
                    with section_card("Rotary Gap", "settings"):
                        rotary_inputs = ui.refreshable(_rotary_inputs)
                        rotary_inputs(state)
                with ui.column().classes("flex-1 sm:min-w-[300px]"):
                    with section_card("Results", "assessment"):
                        rotary_status = ui.label().classes("text-sm mb-2").style(f"color: {TEXT_DIM};")
                        rotary_rows = result_rows(
                            results_grid(),
                            {
                                "ppr": "Presentations / rev",
                                "brk": "Breaks / rev",
                                "bps": "BPS",
                                "tip": "Tip speed",
                                "period": "Firing period",
                                "dwell": "Dwell time",
                                "pct": "% cap charged",
                                "e": "Energy / bang",
                                "vterm": "Terminal voltage",
                                "spark": "Spark length",
                            },
                        )

    def refresh(s: AppState) -> None:
        tank_label.text = _tank_summary(s)
        for status, gap in ((static_status, SparkGapType.STATIC), (rotary_status, SparkGapType.ROTARY)):
            status.text = _gap_status(s, gap)
            status.set_visibility(bool(status.text))
        unit = s.design.unit_system.value
        sym = length_symbol(unit)

        sg = s.outputs.static_gap
        if sg is None:
            clear_rows(static_rows)
        else:
            static_rows["gap"].text = f"{length_in(sg.gap_per_electrode_m, unit):.4f} {sym}"
            static_rows["vbk"].text = f"{sg.breakdown_voltage_v / 1000:.2f} kV"
            static_rows["fires"].text = "yes" if sg.fires else "no — breakdown above V_peak"
            static_rows["pct"].text = f"{sg.percent_cap_charged:.1f} %"
            static_rows["bps"].text = f"{sg.bps:.0f}"
            static_rows["e"].text = f"{sg.effective_cap_energy_j:.3f} J"
            static_rows["vterm"].text = fmt(sg.terminal_voltage_v / 1e3, ".0f", "kV")
            static_rows["spark"].text = f"{length_in(sg.spark_length_m, unit):.1f} {sym}"

        rg = s.outputs.rotary_gap
        if rg is None:
            clear_rows(rotary_rows)
        else:
            rotary_rows["ppr"].text = f"{rg.presentations_per_revolution}"
            rotary_rows["brk"].text = f"{rg.breaks_per_revolution}"
            rotary_rows["bps"].text = f"{rg.bps:.0f}"
            rotary_rows["tip"].text = f"{rg.rotational_speed_m_per_s:.1f} m/s"
            rotary_rows["period"].text = f"{rg.firing_period_s * 1e3:.2f} ms"
            rotary_rows["dwell"].text = f"{rg.mechanical_dwell_time_s * 1e6:.0f} µs"
            rotary_rows["pct"].text = f"{rg.percent_cap_charged:.1f} %"
            rotary_rows["e"].text = f"{rg.effective_cap_energy_j:.3f} J"
            rotary_rows["vterm"].text = fmt(rg.terminal_voltage_v / 1e3, ".0f", "kV")
            rotary_rows["spark"].text = f"{length_in(rg.spark_length_m, unit):.1f} {sym}"

    def rebuild(s: AppState) -> None:
        selector.refresh()
        static_inputs.refresh()
        rotary_inputs.refresh()
        show_gap(resolve_spark_gap_type(s.design))

    state.on_design_replaced(rebuild)
    state.subscribe(refresh)
