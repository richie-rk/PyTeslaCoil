"""Static spark gap calculations.

A static spark gap is a series stack of fixed electrodes that fires when
the tank capacitor voltage reaches the breakdown threshold of the gap.
The classic Tesla coil "multi-gap" is the canonical example.

References
----------
- J.M. Meek and J.D. Craggs, "Electrical Breakdown of Gases" (1953)
- Empirical uniform-field air-breakdown fit used by JavaTC and the Tesla
  coil mailing list FAQ.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import DEFAULT_LINE_FREQUENCY_HZ, PI
from pyteslacoil.engine._checks import require_set
from pyteslacoil.engine.spark_length import spark_length_from_energy, terminal_voltage_estimate
from pyteslacoil.models.spark_gap_model import StaticGapInput, StaticGapOutput

ARC_VOLTAGE_V_PER_M: float = 3_000.0
"""Typical voltage drop along a conducting spark-gap arc (~30 V/cm)."""


def air_breakdown_voltage(gap_m: float) -> float:
    """Empirical breakdown voltage for a uniform air gap at STP.

    Uses the same fit as JavaTC:

        V_break [kV] ≈ 24.22 · g_cm + 6.08 · √g_cm

    valid for moderate gaps (~1 mm to 5 cm). Returns volts.
    """
    if gap_m <= 0:
        return 0.0
    g_cm = gap_m * 100.0
    return (24.22 * g_cm + 6.08 * math.sqrt(g_cm)) * 1000.0


def calculate_static_gap(inp: StaticGapInput) -> StaticGapOutput:
    """Compute static-gap behavior.

    The charging voltage and tank capacitance must be set on ``inp`` (the
    system calculator fills them in from the design). A static gap fires
    once per half line cycle, when the rising charging voltage reaches the
    breakdown voltage; if the breakdown voltage exceeds the peak voltage the
    gap never fires and every per-bang output is zero.
    """
    v_peak = require_set(inp.transformer_voltage_peak, "transformer_voltage_peak")
    c_tank = require_set(inp.tank_capacitance, "tank_capacitance")
    f_line = inp.line_frequency_hz or DEFAULT_LINE_FREQUENCY_HZ

    n_gaps = inp.num_electrodes - 1
    gap_per_electrode = inp.total_gap_spacing / n_gaps

    # Each gap fires when its threshold is reached; the series stack needs the sum.
    v_break_per = air_breakdown_voltage(gap_per_electrode)
    v_break_total = v_break_per * n_gaps

    arc_voltage = ARC_VOLTAGE_V_PER_M * inp.total_gap_spacing

    fires = v_break_total <= v_peak
    # The capacitor charges to V_break before the gap fires (or to V_peak if it never does).
    percent = 100.0 * min(1.0, v_break_total / v_peak)

    if fires:
        # Phase of the charging sine wave at which V reaches V_break.
        phase = math.asin(v_break_total / v_peak)
        time_to_arc: float | None = phase / (2.0 * PI * f_line)
        bps = 2.0 * f_line
        energy = 0.5 * c_tank * v_break_total * v_break_total
    else:
        time_to_arc = None
        bps = 0.0
        energy = 0.0

    return StaticGapOutput(
        gap_per_electrode_m=gap_per_electrode,
        breakdown_voltage_v=v_break_total,
        arc_voltage_v=arc_voltage,
        voltage_gradient_v_per_m=v_break_per / gap_per_electrode,
        arc_voltage_per_unit_v_per_m=arc_voltage / inp.total_gap_spacing,
        fires=fires,
        percent_cap_charged=percent,
        time_to_arc_s=time_to_arc,
        bps=bps,
        effective_cap_energy_j=energy,
        terminal_voltage_v=terminal_voltage_estimate(energy),
        spark_length_m=spark_length_from_energy(bps, energy),
    )
