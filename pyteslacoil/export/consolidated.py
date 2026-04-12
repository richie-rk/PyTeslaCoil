"""Consolidated text export — designed to feel familiar to JavaTC users.

Section names and field names match JavaTC's "View Output" report
wherever possible.
"""

from __future__ import annotations

from io import StringIO

from pyteslacoil.models import CoilDesign, FullSystemOutput
from pyteslacoil.units import meters_to_inches


def _section(buf: StringIO, title: str) -> None:
    buf.write("\n")
    buf.write("=" * 60 + "\n")
    buf.write(f" {title}\n")
    buf.write("=" * 60 + "\n")


def _kv(buf: StringIO, key: str, value: str) -> None:
    buf.write(f"  {key:<32} {value}\n")


def to_text(design: CoilDesign, outputs: FullSystemOutput) -> str:
    buf = StringIO()
    buf.write(f"PyTeslaCoil — {design.name}\n")
    buf.write(f"Unit system: {design.unit_system.value}\n")

    # ----- Secondary -------------------------------------------------------
    if design.secondary and outputs.secondary:
        s, o = design.secondary, outputs.secondary
        _section(buf, "Secondary Coil")
        _kv(buf, "Radius (top / bottom)", f"{meters_to_inches(s.radius_1):.4f} / {meters_to_inches(s.radius_2):.4f} in")
        _kv(buf, "Winding height", f"{meters_to_inches(o.winding_height_m):.4f} in")
        _kv(buf, "Turns", f"{s.turns}")
        _kv(buf, "Wire", f"AWG {s.wire_awg}")
        _kv(buf, "Inductance", f"{o.inductance_mh:.4f} mH")
        _kv(buf, "Self capacitance", f"{o.self_capacitance_pf:.3f} pF")
        _kv(buf, "Resonant frequency", f"{o.resonant_frequency_khz:.3f} kHz")
        if o.system_resonant_frequency_khz:
            _kv(buf, "Resonant frequency (with topload)", f"{o.system_resonant_frequency_khz:.3f} kHz")
        _kv(buf, "Wire length", f"{o.wire_length_m:.2f} m  ({o.wire_length_ft:.2f} ft)")
        _kv(buf, "DC resistance", f"{o.dc_resistance_ohms:.3f} Ω")
        _kv(buf, "AC resistance", f"{o.ac_resistance_ohms:.3f} Ω")
        _kv(buf, "Q factor", f"{o.q_factor:.0f}")
        _kv(buf, "Impedance", f"{o.impedance_ohms:,.0f} Ω")

    # ----- Primary ---------------------------------------------------------
    if design.primary and outputs.primary:
        p, o = design.primary, outputs.primary
        _section(buf, "Primary Coil")
        _kv(buf, "Geometry", o.primary_geometry.value)
        _kv(buf, "Radius (inner / outer)", f"{meters_to_inches(p.radius_1):.4f} / {meters_to_inches(p.radius_2):.4f} in")
        _kv(buf, "Height (start / end)", f"{meters_to_inches(p.height_1):.4f} / {meters_to_inches(p.height_2):.4f} in")
        _kv(buf, "Turns", f"{p.turns:.4f}")
        _kv(buf, "Conductor diameter", f"{meters_to_inches(p.wire_diameter):.4f} in")
        _kv(buf, "Tank capacitance", f"{p.capacitance * 1e9:.3f} nF")
        _kv(buf, "Coil inductance", f"{o.inductance_uh:.3f} µH")
        _kv(buf, "Lead inductance", f"{o.lead_inductance_uh:.3f} µH")
        _kv(buf, "Total inductance", f"{o.total_inductance_uh:.3f} µH")
        _kv(buf, "Resonant frequency", f"{o.resonant_frequency_khz:.3f} kHz")
        if o.tuning_ratio:
            _kv(buf, "Tuning ratio (f_sec / f_pri)", f"{o.tuning_ratio:.4f}")
        _kv(buf, "Impedance", f"{o.impedance_ohms:,.1f} Ω")

    # ----- Topload ---------------------------------------------------------
    if design.topload and outputs.topload:
        t, o = design.topload, outputs.topload
        _section(buf, "Topload")
        _kv(buf, "Type", o.topload_type.value)
        if t.major_diameter:
            _kv(buf, "Major diameter", f"{meters_to_inches(t.major_diameter):.3f} in")
        if t.minor_diameter:
            _kv(buf, "Minor diameter", f"{meters_to_inches(t.minor_diameter):.3f} in")
        if t.sphere_diameter:
            _kv(buf, "Sphere diameter", f"{meters_to_inches(t.sphere_diameter):.3f} in")
        _kv(buf, "Height", f"{meters_to_inches(t.height):.3f} in")
        _kv(buf, "Capacitance", f"{o.capacitance_pf:.3f} pF")

    # ----- Coupling --------------------------------------------------------
    if outputs.coupling:
        c = outputs.coupling
        _section(buf, "Coupling")
        _kv(buf, "Coupling coefficient k", f"{c.coupling_coefficient:.4f}")
        _kv(buf, "Mutual inductance", f"{c.mutual_inductance_uh:.4f} µH")
        _kv(buf, "Energy transfer time", f"{c.energy_transfer_time_s * 1e6:.3f} µs")
        _kv(buf, "Cycles to transfer", f"{c.energy_transfer_cycles:.2f}")

    # ----- Transformer -----------------------------------------------------
    if design.transformer and outputs.transformer:
        t, o = design.transformer, outputs.transformer
        _section(buf, "Transformer")
        _kv(buf, "Type", t.transformer_type.value)
        _kv(buf, "Output voltage (RMS)", f"{t.output_voltage:,.0f} V")
        _kv(buf, "Output voltage (peak)", f"{o.output_voltage_peak:,.0f} V")
        _kv(buf, "Output current", f"{t.output_current * 1000:.1f} mA")
        _kv(buf, "VA rating", f"{o.va_rating:.0f} VA")
        _kv(buf, "Impedance", f"{o.impedance_ohms:,.0f} Ω")
        _kv(buf, "Resonant cap", f"{o.resonant_cap_size_nf:.3f} nF")
        _kv(buf, "LTR cap (1.6×)", f"{o.ltr_cap_size_nf:.3f} nF")

    # ----- Static gap ------------------------------------------------------
    if outputs.static_gap:
        g = outputs.static_gap
        _section(buf, "Static Spark Gap")
        _kv(buf, "Gap per electrode", f"{g.gap_per_electrode_m * 1000:.3f} mm")
        _kv(buf, "Breakdown voltage", f"{g.breakdown_voltage_v / 1000:.2f} kV")
        _kv(buf, "% capacitor charged", f"{g.percent_cap_charged:.1f} %")
        _kv(buf, "Energy / bang", f"{g.effective_cap_energy_j:.3f} J")
        _kv(buf, "BPS", f"{g.bps:.0f}")
        _kv(buf, "Spark length", f"{g.spark_length_m / 0.0254:.1f} in")

    # ----- Rotary gap ------------------------------------------------------
    if outputs.rotary_gap:
        r = outputs.rotary_gap
        _section(buf, "Rotary Spark Gap")
        _kv(buf, "Presentations / rev", f"{r.presentations_per_revolution}")
        _kv(buf, "BPS", f"{r.bps:.0f}")
        _kv(buf, "Tip speed", f"{r.rotational_speed_m_per_s:.1f} m/s")
        _kv(buf, "% capacitor charged", f"{r.percent_cap_charged:.1f} %")
        _kv(buf, "Energy / bang", f"{r.effective_cap_energy_j:.3f} J")
        _kv(buf, "Spark length", f"{r.spark_length_m / 0.0254:.1f} in")

    # ----- Environment -----------------------------------------------------
    if outputs.environment:
        e = outputs.environment
        _section(buf, "Environment")
        _kv(buf, "Proximity correction", f"{e.proximity_correction_factor:.3f}")
        _kv(buf, "Notes", e.notes)

    # ----- System summary --------------------------------------------------
    _section(buf, "System Summary")
    if outputs.system_resonant_frequency_khz:
        _kv(buf, "System resonant frequency", f"{outputs.system_resonant_frequency_khz:.3f} kHz")
    if outputs.tuning_ratio:
        _kv(buf, "Tuning ratio", f"{outputs.tuning_ratio:.4f}")
    if outputs.estimated_spark_length_in:
        _kv(buf, "Estimated spark length", f"{outputs.estimated_spark_length_in:.1f} in")

    return buf.getvalue()
