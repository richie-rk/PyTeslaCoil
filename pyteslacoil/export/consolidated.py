"""Consolidated text export — designed to feel familiar to JavaTC users.

Section names and field names match JavaTC's "View Output" report
wherever possible. Lengths are reported in the design's unit system.
"""

from __future__ import annotations

import math
from io import StringIO

from pyteslacoil.constants import M_TO_FT
from pyteslacoil.engine.transformer import LTR_FACTOR
from pyteslacoil.models import CoilDesign, FullSystemOutput, ToploadType
from pyteslacoil.units import length_in, length_symbol

_RULE = "=" * 60


class _Report:
    def __init__(self, unit: str) -> None:
        self.buf = StringIO()
        self.unit = unit
        self.symbol = length_symbol(unit)

    def line(self, text: str = "") -> None:
        self.buf.write(text + "\n")

    def section(self, title: str) -> None:
        self.line()
        self.line(_RULE)
        self.line(f" {title}")
        self.line(_RULE)

    def kv(self, key: str, value: str) -> None:
        self.line(f"  {key:<34} {value}")

    def length(self, value_m: float, decimals: int = 3) -> str:
        return f"{length_in(value_m, self.unit):.{decimals}f} {self.symbol}"

    def lengths(self, a_m: float, b_m: float, decimals: int = 3) -> str:
        a, b = length_in(a_m, self.unit), length_in(b_m, self.unit)
        return f"{a:.{decimals}f} / {b:.{decimals}f} {self.symbol}"


def to_text(design: CoilDesign, outputs: FullSystemOutput) -> str:
    """Render ``design`` and its ``outputs`` as a plain-text report."""
    r = _Report(design.unit_system.value)
    r.line(f"PyTeslaCoil — {design.name}")
    r.line(f"Unit system: {design.unit_system.value}")

    # ----- Secondary -------------------------------------------------------
    if design.secondary and outputs.secondary:
        sec_in, sec_out = design.secondary, outputs.secondary
        r.section("Secondary Coil")
        r.kv("Radius (bottom / top)", r.lengths(sec_in.radius_1, sec_in.radius_2, 4))
        r.kv("Winding height (start / end)", r.lengths(sec_in.height_1, sec_in.height_2))
        r.kv("Winding length", r.length(sec_out.winding_height_m))
        r.kv("Turns", f"{sec_in.turns}")
        r.kv("Wire", f"AWG {sec_in.wire_awg}")
        r.kv("Inductance", f"{sec_out.inductance_mh:.4f} mH")
        r.kv("Self capacitance", f"{sec_out.self_capacitance_pf:.3f} pF")
        r.kv("Resonant frequency (bare)", f"{sec_out.resonant_frequency_khz:.3f} kHz")
        if sec_out.system_resonant_frequency_khz is not None:
            r.kv("Resonant frequency (with topload)", f"{sec_out.system_resonant_frequency_khz:.3f} kHz")
        r.kv("Wire length", f"{sec_out.wire_length_m:.2f} m  ({sec_out.wire_length_ft:.2f} ft)")
        r.kv("DC resistance", f"{sec_out.dc_resistance_ohms:.3f} Ω")
        r.kv("AC resistance (skin effect)", f"{sec_out.ac_resistance_ohms:.3f} Ω")
        r.kv("Q factor (bare)", f"{sec_out.q_factor:.0f}")
        r.kv("Impedance", f"{sec_out.impedance_ohms:,.0f} Ω")

    # ----- Primary ---------------------------------------------------------
    if design.primary and outputs.primary:
        pri_in, pri_out = design.primary, outputs.primary
        r.section("Primary Coil")
        r.kv("Geometry", pri_out.primary_geometry.value)
        r.kv("Radius (start / end)", r.lengths(pri_in.radius_1, pri_in.radius_2, 4))
        r.kv("Height (start / end)", r.lengths(pri_in.height_1, pri_in.height_2, 4))
        r.kv("Turns", f"{pri_in.turns:.4f}")
        tuned = outputs.tuned_primary
        if tuned is not None:
            r.kv("Auto-tuned turns", f"{tuned.turns:.4f}")
            r.kv("Auto-tuned end (radius / height)", r.lengths(tuned.radius_2, tuned.height_2, 4))
        r.kv("Conductor", f"{pri_in.conductor_type.value}, {r.length(pri_in.wire_diameter, 4)}")
        r.kv("Tank capacitance", f"{pri_in.capacitance * 1e9:.3f} nF")
        r.kv("Coil inductance", f"{pri_out.inductance_uh:.3f} µH")
        r.kv("Lead inductance", f"{pri_out.lead_inductance_uh:.3f} µH")
        r.kv("Total inductance", f"{pri_out.total_inductance_uh:.3f} µH")
        r.kv("Resonant frequency", f"{pri_out.resonant_frequency_khz:.3f} kHz")
        if pri_out.tuning_ratio is not None:
            r.kv("Tuning ratio (f_sec / f_pri)", f"{pri_out.tuning_ratio:.4f}")
        r.kv("Impedance", f"{pri_out.impedance_ohms:,.1f} Ω")
        r.kv("Wire length", f"{pri_out.wire_length_m:.2f} m  ({pri_out.wire_length_m * M_TO_FT:.2f} ft)")
        r.kv("DC resistance", f"{pri_out.dc_resistance_ohms:.4f} Ω")

    # ----- Topload ---------------------------------------------------------
    if design.topload and outputs.topload:
        top_in, top_out = design.topload, outputs.topload
        r.section("Topload")
        r.kv("Type", top_out.topload_type.value)
        if top_in.topload_type == ToploadType.TOROID and top_in.major_diameter and top_in.minor_diameter:
            r.kv("Major / minor diameter", r.lengths(top_in.major_diameter, top_in.minor_diameter))
        if top_in.topload_type == ToploadType.SPHERE and top_in.sphere_diameter:
            r.kv("Sphere diameter", r.length(top_in.sphere_diameter))
        if top_in.height is not None:
            r.kv("Height", r.length(top_in.height))
        r.kv("Capacitance (free space)", f"{top_out.capacitance_pf:.3f} pF")
        effective_pf = outputs.effective_topload_capacitance_pf
        if effective_pf is not None and not math.isclose(effective_pf, top_out.capacitance_pf):
            r.kv("Capacitance (with environment)", f"{effective_pf:.3f} pF")

    # ----- Coupling --------------------------------------------------------
    if outputs.coupling:
        cpl = outputs.coupling
        r.section("Coupling")
        r.kv("Coupling coefficient k", f"{cpl.coupling_coefficient:.4f}")
        r.kv("Mutual inductance", f"{cpl.mutual_inductance_uh:.4f} µH")
        if cpl.energy_transfer_time_s is not None and cpl.energy_transfer_cycles is not None:
            r.kv("Energy transfer time", f"{cpl.energy_transfer_time_s * 1e6:.3f} µs")
            r.kv("Cycles to transfer", f"{cpl.energy_transfer_cycles:.2f}")

    # ----- Transformer -----------------------------------------------------
    if design.transformer and outputs.transformer:
        xf_in, xf_out = design.transformer, outputs.transformer
        r.section("Transformer")
        r.kv("Type", xf_in.transformer_type.value)
        r.kv("Output voltage (RMS)", f"{xf_in.output_voltage:,.0f} V")
        r.kv("Output voltage (peak)", f"{xf_out.output_voltage_peak:,.0f} V")
        r.kv("Output current", f"{xf_in.output_current * 1000:.1f} mA")
        r.kv("VA rating", f"{xf_out.va_rating:.0f} VA")
        r.kv("Input current", f"{xf_out.input_current_a:.2f} A at {xf_in.input_voltage:.0f} V")
        r.kv("Impedance", f"{xf_out.impedance_ohms:,.0f} Ω")
        r.kv("Resonant cap", f"{xf_out.resonant_cap_size_nf:.3f} nF")
        r.kv(f"LTR cap ({LTR_FACTOR:g}×)", f"{xf_out.ltr_cap_size_nf:.3f} nF")

    # ----- Static gap ------------------------------------------------------
    if outputs.static_gap:
        sg = outputs.static_gap
        r.section("Static Spark Gap")
        r.kv("Gap per electrode", r.length(sg.gap_per_electrode_m, 4))
        r.kv("Breakdown voltage", f"{sg.breakdown_voltage_v / 1000:.2f} kV")
        r.kv("Fires", "yes" if sg.fires else "no (breakdown voltage above peak voltage)")
        r.kv("% capacitor charged", f"{sg.percent_cap_charged:.1f} %")
        r.kv("Energy / bang", f"{sg.effective_cap_energy_j:.3f} J")
        r.kv("BPS", f"{sg.bps:.0f}")
        r.kv("Spark length", r.length(sg.spark_length_m, 1))

    # ----- Rotary gap ------------------------------------------------------
    if outputs.rotary_gap:
        rg = outputs.rotary_gap
        r.section("Rotary Spark Gap")
        r.kv("Presentations / rev", f"{rg.presentations_per_revolution}")
        r.kv("Breaks / rev", f"{rg.breaks_per_revolution}")
        r.kv("BPS", f"{rg.bps:.0f}")
        r.kv("Tip speed", f"{rg.rotational_speed_m_per_s:.1f} m/s")
        r.kv("Dwell time", f"{rg.mechanical_dwell_time_s * 1e6:.1f} µs")
        r.kv("% capacitor charged", f"{rg.percent_cap_charged:.1f} %")
        r.kv("Energy / bang", f"{rg.effective_cap_energy_j:.3f} J")
        r.kv("Spark length", r.length(rg.spark_length_m, 1))

    # ----- Environment -----------------------------------------------------
    if outputs.environment:
        env = outputs.environment
        r.section("Environment")
        r.kv("Proximity correction", f"{env.proximity_correction_factor:.3f}")
        r.kv("Notes", env.notes)

    # ----- System summary --------------------------------------------------
    r.section("System Summary")
    if outputs.active_spark_gap is not None:
        r.kv("Spark gap", outputs.active_spark_gap.value)
    if outputs.system_resonant_frequency_khz is not None:
        r.kv("System resonant frequency", f"{outputs.system_resonant_frequency_khz:.3f} kHz")
    if outputs.tuning_ratio is not None:
        r.kv("Tuning ratio", f"{outputs.tuning_ratio:.4f}")
    if outputs.estimated_spark_length_m is not None:
        r.kv("Estimated spark length", r.length(outputs.estimated_spark_length_m, 1))
    if outputs.estimated_terminal_voltage_v is not None:
        r.kv("Estimated terminal voltage", f"{outputs.estimated_terminal_voltage_v / 1e3:,.0f} kV")

    if outputs.warnings:
        r.section("Warnings")
        for warning in outputs.warnings:
            r.line(f"  - {warning}")

    return r.buf.getvalue()
