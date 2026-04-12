"""Medhurst self-capacitance coefficients.

A single-layer solenoid has a distributed self-capacitance that is well
approximated by an empirical relation due to R.G. Medhurst (1947):

    C_self [pF] = H * D [cm]

where ``H`` is a dimensionless coefficient that depends on the ratio of the
winding length to the coil diameter (``L/D``). This module provides the
classical Medhurst lookup table and a linear interpolator built on
``numpy.interp``.

Source
------
R.G. Medhurst, "H.F. Resistance and Self-Capacitance of Single-Layer
Solenoids", Wireless Engineer, 24 (Feb 1947), pp. 35-43; (Mar 1947),
pp. 80-92.
"""

from __future__ import annotations

import numpy as np

# (L/D ratio, Medhurst H coefficient) pairs.
MEDHURST_TABLE: list[tuple[float, float]] = [
    (0.10, 0.96),
    (0.15, 0.79),
    (0.20, 0.70),
    (0.25, 0.64),
    (0.30, 0.60),
    (0.35, 0.57),
    (0.40, 0.54),
    (0.50, 0.50),
    (0.60, 0.47),
    (0.70, 0.45),
    (0.80, 0.44),
    (0.90, 0.43),
    (1.00, 0.42),
    (1.50, 0.40),
    (2.00, 0.39),
    (2.50, 0.39),
    (3.00, 0.39),
    (3.50, 0.39),
    (4.00, 0.38),
    (5.00, 0.38),
]

# Pre-split into numpy arrays for the interpolator.
_RATIOS = np.array([row[0] for row in MEDHURST_TABLE], dtype=float)
_COEFFS = np.array([row[1] for row in MEDHURST_TABLE], dtype=float)


def medhurst_coefficient(length_to_diameter_ratio: float) -> float:
    """Return the Medhurst H coefficient for a given ``L/D`` ratio.

    Linear interpolation is used between table entries; values outside the
    table range are clamped to the nearest endpoint (this is the convention
    used by JavaTC and the underlying Medhurst paper).
    """
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
    diameter_cm = diameter_m * 100.0
    ratio = length_m / diameter_m
    h = medhurst_coefficient(ratio)
    return h * diameter_cm


def self_capacitance_farads(length_m: float, diameter_m: float) -> float:
    """Same as :func:`self_capacitance_pf` but returns farads."""
    return self_capacitance_pf(length_m, diameter_m) * 1e-12
