"""Medhurst self-capacitance coefficients.

A single-layer solenoid has a distributed self-capacitance that is well
approximated by an empirical relation due to R.G. Medhurst (1947):

    C_self [pF] = H · D [cm]

where ``H`` depends on the ratio of the winding length to the coil diameter
(``l/D``). ``H`` has a broad minimum of 0.46 around ``l/D ≈ 1`` and grows
for both short and long coils — long Tesla coil secondaries (``l/D`` of
3–6) have ``H`` of roughly 0.6–0.9.

Source
------
R.G. Medhurst, "H.F. Resistance and Self-Capacitance of Single-Layer
Solenoids", Wireless Engineer, 24 (Feb 1947), pp. 35-43; (Mar 1947),
pp. 80-92. Values as reproduced in the Tesla Coil Mailing List archives.
"""

from __future__ import annotations

import numpy as np

# (l/D ratio, Medhurst H coefficient) pairs.
MEDHURST_TABLE: list[tuple[float, float]] = [
    (0.10, 0.96),
    (0.15, 0.79),
    (0.20, 0.70),
    (0.25, 0.64),
    (0.30, 0.60),
    (0.35, 0.57),
    (0.40, 0.54),
    (0.45, 0.52),
    (0.50, 0.50),
    (0.60, 0.48),
    (0.70, 0.47),
    (0.80, 0.46),
    (0.90, 0.46),
    (1.00, 0.46),
    (1.50, 0.47),
    (2.00, 0.50),
    (2.50, 0.56),
    (3.00, 0.61),
    (3.50, 0.67),
    (4.00, 0.72),
    (4.50, 0.77),
    (5.00, 0.81),
    (6.00, 0.92),
    (7.00, 1.01),
    (8.00, 1.12),
    (9.00, 1.22),
    (10.0, 1.32),
]

LONG_COIL_SLOPE: float = 0.1126
"""dH / d(l/D) for long coils (Medhurst's asymptote ``C ≈ 0.1126 · l[cm]`` pF)."""

# Pre-split into numpy arrays for the interpolator.
_RATIOS = np.array([row[0] for row in MEDHURST_TABLE], dtype=float)
_COEFFS = np.array([row[1] for row in MEDHURST_TABLE], dtype=float)


def medhurst_coefficient(length_to_diameter_ratio: float) -> float:
    """Return the Medhurst H coefficient for a given ``l/D`` ratio.

    Linear interpolation is used between table entries. Below the table
    (``l/D < 0.1``) the first value is used; beyond it (``l/D > 10``) ``H``
    grows linearly with Medhurst's long-coil slope, which reproduces his
    ``H ≈ 5.8`` at ``l/D = 50``.
    """
    if length_to_diameter_ratio > _RATIOS[-1]:
        excess = length_to_diameter_ratio - _RATIOS[-1]
        return float(_COEFFS[-1] + LONG_COIL_SLOPE * excess)
    return float(np.interp(length_to_diameter_ratio, _RATIOS, _COEFFS))


def self_capacitance_pf(length_m: float, diameter_m: float) -> float:
    """Compute solenoid self-capacitance using the Medhurst formula.

    Parameters
    ----------
    length_m
        Winding length in meters.
    diameter_m
        Coil diameter (over the wire centers) in meters.

    Returns
    -------
    float
        Self-capacitance in picofarads.
    """
    if diameter_m <= 0:
        raise ValueError("diameter_m must be positive")
    if length_m < 0:
        raise ValueError("length_m must not be negative")
    diameter_cm = diameter_m * 100.0
    h = medhurst_coefficient(length_m / diameter_m)
    return h * diameter_cm


def self_capacitance_farads(length_m: float, diameter_m: float) -> float:
    """Same as :func:`self_capacitance_pf` but returns farads."""
    return self_capacitance_pf(length_m, diameter_m) * 1e-12
