"""Static spark gap calculations.

A static spark gap is a series stack of fixed electrodes that fires when
the tank capacitor voltage reaches the breakdown threshold of the gap.
The classic Tesla coil "multi-gap" is the canonical example.

References
----------
- J.M. Meek and J.D. Craggs, "Electrical Breakdown of Gases" (1953)
- Paschen's law (~1889) and the empirical air-breakdown fits used by
  JavaTC and the Tesla coil mailing list FAQ.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import PI
from pyteslacoil.models.spark_gap_model import StaticGapInput, StaticGapOutput


def air_breakdown_voltage(gap_m: float) -> float:
    """Empirical breakdown voltage for a uniform air gap at STP.

    Uses the same fit as JavaTC:

        V_break [kV] ≈ 24.22 · g_cm + 6.08 · √g_cm

    valid for moderate gaps (~1 mm to 5 cm). Returns volts.
    """
    if gap_m <= 0:
        return 0.0
    g_cm = gap_m * 100.0
    v_kv = 24.22 * g_cm + 6.08 * math.sqrt(g_cm)
    return v_kv * 1000.0


def calculate_static_gap(inp: StaticGapInput) -> StaticGapOutput:
    """Compute static-gap behavior.

    Inputs include the transformer peak voltage and tank capacitance, so
    we can also estimate cap-charge percentage and energy per bang.
    """
    n_gaps = max(inp.num_electrodes - 1, 1)
    gap_per_electrode = inp.total_gap_spacing / n_gaps

    # Each gap fires when its threshold is reached. The total breakdown
    # voltage is just the sum.
    v_break_per = air_breakdown_voltage(gap_per_electrode)
    v_break_total = v_break_per * n_gaps

    # Arc voltage during conduction. Empirically ~30 V/cm for an arc.
    arc_voltage = 30.0 * gap_per_electrode * 100.0 * n_gaps

    voltage_gradient = (
        v_break_per / gap_per_electrode if gap_per_electrode > 0 else 0.0
    )
    arc_voltage_per_unit = (
        arc_voltage / inp.total_gap_spacing if inp.total_gap_spacing > 0 else 0.0
    )

    # Percent charged: V_break / V_peak (capped at 100 %).
    if inp.transformer_voltage_peak > 0:
        percent = min(100.0, 100.0 * v_break_total / inp.transformer_voltage_peak)
    else:
        percent = 0.0

    # Time to arc — depends on charging waveform; for a 60 Hz sine the
    # half cycle is 1/(2 f_line). The phase angle at which V reaches
    # V_break is asin(V_break / V_peak).
    if inp.transformer_voltage_peak > 0 and v_break_total <= inp.transformer_voltage_peak:
        phase = math.asin(v_break_total / inp.transformer_voltage_peak)
        time_to_arc = phase / (2.0 * PI * inp.line_frequency_hz)
    else:
        time_to_arc = 1.0 / (2.0 * inp.line_frequency_hz)

    # BPS: a static gap fires twice per line cycle in steady state.
    bps = 2.0 * inp.line_frequency_hz

    # Effective cap energy at fire.
    v_eff = inp.transformer_voltage_peak * (percent / 100.0)
    energy = 0.5 * inp.tank_capacitance * v_eff * v_eff

    # Terminal voltage and spark length using Freau (see spark_length).
    from pyteslacoil.engine.spark_length import (
        spark_length_from_energy,
        terminal_voltage_estimate,
    )

    v_term = terminal_voltage_estimate(energy)
    spark_len = spark_length_from_energy(bps, energy)

    return StaticGapOutput(
        gap_per_electrode_m=gap_per_electrode,
        breakdown_voltage_v=v_break_total,
        arc_voltage_v=arc_voltage,
        voltage_gradient_v_per_m=voltage_gradient,
        arc_voltage_per_unit_v_per_m=arc_voltage_per_unit,
        percent_cap_charged=percent,
        time_to_arc_s=time_to_arc,
        bps=bps,
        effective_cap_energy_j=energy,
        terminal_voltage_v=v_term,
        spark_length_m=spark_len,
    )
