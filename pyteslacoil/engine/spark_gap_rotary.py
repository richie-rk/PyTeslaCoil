"""Rotary spark gap calculations.

A rotary gap uses a spinning disc with electrodes that present themselves
to fixed stationary electrodes; each presentation is a potential firing
event. BPS is much higher than a static gap and is set by the disc RPM.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import PI
from pyteslacoil.models.spark_gap_model import RotaryGapInput, RotaryGapOutput


def calculate_rotary_gap(inp: RotaryGapInput) -> RotaryGapOutput:
    presentations = inp.num_rotating_electrodes * inp.num_stationary_electrodes
    rps = inp.disc_rpm / 60.0
    bps = presentations * rps

    tip_speed = PI * inp.rotating_path_diameter * rps  # m/s
    firing_rate = 1.0 / bps if bps > 0 else float("inf")

    combined = (
        inp.rotating_electrode_diameter + inp.stationary_electrode_diameter
    )
    dwell = combined / tip_speed if tip_speed > 0 else 0.0

    # Cap charge fraction. The cap charges at the line frequency to V_peak;
    # if it fires faster than the line cycle, the charge is fractional.
    half_cycle = 1.0 / (2.0 * inp.line_frequency_hz)
    if firing_rate >= half_cycle:
        percent = 100.0
    else:
        # Sinusoidal charge: V(t) = V_peak · sin(2π f_line · t)
        ratio = math.sin(2.0 * PI * inp.line_frequency_hz * firing_rate)
        percent = max(0.0, min(100.0, abs(ratio) * 100.0))

    v_eff = inp.transformer_voltage_peak * (percent / 100.0)
    energy = 0.5 * inp.tank_capacitance * v_eff * v_eff

    from pyteslacoil.engine.spark_length import (
        spark_length_from_energy,
        terminal_voltage_estimate,
    )

    v_term = terminal_voltage_estimate(energy)
    spark_len = spark_length_from_energy(bps, energy)

    return RotaryGapOutput(
        presentations_per_revolution=presentations,
        bps=bps,
        rotational_speed_m_per_s=tip_speed,
        firing_rate_s=firing_rate,
        mechanical_dwell_time_s=dwell,
        percent_cap_charged=percent,
        effective_cap_energy_j=energy,
        terminal_voltage_v=v_term,
        spark_length_m=spark_len,
    )
