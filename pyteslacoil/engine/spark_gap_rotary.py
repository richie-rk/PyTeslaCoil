"""Rotary spark gap calculations.

A rotary gap uses a spinning disc with electrodes that present themselves
to fixed stationary electrodes. Stationary electrodes are wired as series
pairs (the usual SRSG/ARSG arrangement): both electrodes of a pair line up
with rotating electrodes at the same moment and fire as one break. With the
common two stationary electrodes, BPS = rotating electrodes × RPM / 60 —
e.g. four rotating electrodes at 1800 RPM give the classic synchronous
120 BPS. A single stationary electrode is a gap to a brushed (grounded)
rotor, which also gives one break per rotating-electrode pass.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import DEFAULT_LINE_FREQUENCY_HZ, PI
from pyteslacoil.engine._checks import require_set
from pyteslacoil.engine.spark_length import spark_length_from_energy, terminal_voltage_estimate
from pyteslacoil.models.spark_gap_model import RotaryGapInput, RotaryGapOutput


def charge_fraction(firing_period_s: float, line_frequency_hz: float) -> float:
    """Fraction of the peak voltage the tank capacitor reaches between firings.

    Model: after each firing the capacitor recharges from 0 V following the
    rising part of the line waveform, ``V(t) = V_peak · sin(2π f t)``, which
    reaches the peak after a quarter cycle. Firing periods of a quarter line
    cycle or longer therefore reach full charge.
    """
    quarter_cycle = 1.0 / (4.0 * line_frequency_hz)
    return math.sin(2.0 * PI * line_frequency_hz * min(firing_period_s, quarter_cycle))


def calculate_rotary_gap(inp: RotaryGapInput) -> RotaryGapOutput:
    """Compute rotary-gap firing rate, dwell, charge and energy per bang.

    The charging voltage and tank capacitance must be set on ``inp`` (the
    system calculator fills them in from the design).
    """
    v_peak = require_set(inp.transformer_voltage_peak, "transformer_voltage_peak")
    c_tank = require_set(inp.tank_capacitance, "tank_capacitance")
    f_line = inp.line_frequency_hz or DEFAULT_LINE_FREQUENCY_HZ

    presentations = inp.num_rotating_electrodes * inp.num_stationary_electrodes
    series_pairs = max(1, inp.num_stationary_electrodes // 2)
    breaks_per_rev = inp.num_rotating_electrodes * series_pairs

    rps = inp.disc_rpm / 60.0
    bps = breaks_per_rev * rps
    firing_period = 1.0 / bps

    tip_speed = PI * inp.rotating_path_diameter * rps  # m/s
    dwell = (inp.rotating_electrode_diameter + inp.stationary_electrode_diameter) / tip_speed

    fraction = charge_fraction(firing_period, f_line)
    v_eff = v_peak * fraction
    energy = 0.5 * c_tank * v_eff * v_eff

    return RotaryGapOutput(
        presentations_per_revolution=presentations,
        breaks_per_revolution=breaks_per_rev,
        bps=bps,
        rotational_speed_m_per_s=tip_speed,
        firing_period_s=firing_period,
        mechanical_dwell_time_s=dwell,
        percent_cap_charged=100.0 * fraction,
        effective_cap_energy_j=energy,
        terminal_voltage_v=terminal_voltage_estimate(energy),
        spark_length_m=spark_length_from_energy(bps, energy),
    )
