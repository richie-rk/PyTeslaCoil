"""Empirical spark length estimation.

The classical Freau formula:

    L_spark [in] ≈ 1.7 · √P [W]      (input power based)
    L_spark [in] ≈ 1.7 · √(BPS · E_bang)  (energy based)

Both forms agree to within ~10 % for typical Tesla coils. We return
meters internally.
"""

from __future__ import annotations

import math


def spark_length_from_power(input_power_watts: float) -> float:
    """Freau spark length from input power. Returns meters."""
    if input_power_watts <= 0:
        return 0.0
    inches = 1.7 * math.sqrt(input_power_watts)
    return inches * 0.0254


def spark_length_from_energy(bps: float, energy_per_bang_j: float) -> float:
    """Freau spark length from BPS and per-bang energy. Returns meters."""
    if bps <= 0 or energy_per_bang_j <= 0:
        return 0.0
    inches = 1.7 * math.sqrt(bps * energy_per_bang_j)
    return inches * 0.0254


def terminal_voltage_estimate(energy_per_bang_j: float) -> float:
    """Very rough estimate of the secondary terminal voltage.

    Assumes a topload self-capacitance of 30 pF (typical) and that the
    bang energy ends up entirely on the topload. Useful as a sanity check
    for the UI; not a substitute for a full transient simulation.
    """
    if energy_per_bang_j <= 0:
        return 0.0
    c_assumed = 30e-12
    # E = ½ C V²  →  V = √(2E / C)
    return math.sqrt(2.0 * energy_per_bang_j / c_assumed)


def estimate_spark_length(
    input_power_watts: float,
    bps: float = 0.0,
    energy_per_bang_j: float = 0.0,
) -> float:
    """Combined helper. Prefers the energy form when both are provided."""
    if bps > 0 and energy_per_bang_j > 0:
        return spark_length_from_energy(bps, energy_per_bang_j)
    return spark_length_from_power(input_power_watts)
