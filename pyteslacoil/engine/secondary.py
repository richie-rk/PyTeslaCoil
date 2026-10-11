"""Secondary coil calculations.

This module computes the inductance, self-capacitance, resonant frequency,
DC and AC resistance, Q factor, and impedance of a single-layer secondary
coil. Both straight solenoids and conical coils are supported.

All inputs are in SI units (meters). Convert from inches/cm at the
calling boundary using helpers in :mod:`pyteslacoil.units`.

References
----------
- H.A. Wheeler, "Simple Inductance Formulas for Radio Coils", Proc. IRE,
  16 (Oct 1928), pp. 1398-1400.  Used here in its SI form.
- R.G. Medhurst, "H.F. Resistance and Self-Capacitance of Single-Layer
  Solenoids", Wireless Engineer, 24 (1947).  Implemented in
  :mod:`pyteslacoil.engine.medhurst`.
- S. Ramo, J.R. Whinnery, T. Van Duzer, "Fields and Waves in Communication
  Electronics" — internal impedance of a round wire (Bessel solution).
"""

from __future__ import annotations

import math

from scipy.special import jve

from pyteslacoil.constants import (
    COPPER_PERMEABILITY,
    COPPER_REFERENCE_TEMP_C,
    COPPER_RESISTIVITY,
    COPPER_TEMP_COEFF,
    DEFAULT_TEMP_C,
    MU_0,
    PI,
)
from pyteslacoil.engine.inductance import wheeler_solenoid_inductance
from pyteslacoil.engine.medhurst import self_capacitance_farads
from pyteslacoil.engine.resonance import characteristic_impedance, resonant_frequency
from pyteslacoil.models.enums import CoilGeometry
from pyteslacoil.models.secondary_model import SecondaryInput, SecondaryOutput
from pyteslacoil.units import lengths_equal
from pyteslacoil.wire_data import bare_diameter_m, resistance_per_meter

__all__ = [
    "ac_resistance",
    "calculate_secondary",
    "conical_inductance",
    "copper_resistivity",
    "dc_resistance",
    "detect_secondary_geometry",
    "skin_depth",
    "wheeler_solenoid_inductance",
    "wire_length_for_secondary",
]


def detect_secondary_geometry(radius_1: float, radius_2: float) -> CoilGeometry:
    """Classify the secondary coil from its bottom/top radii."""
    if lengths_equal(radius_1, radius_2):
        return CoilGeometry.SOLENOID
    if radius_2 > radius_1:
        return CoilGeometry.CONICAL
    return CoilGeometry.INVERSE_CONICAL


def conical_inductance(
    turns: float,
    radius_1_m: float,
    radius_2_m: float,
    length_m: float,
) -> float:
    """Inductance of a conical (or inverse conical) single-layer coil.

    Approximation: average the radii and reuse the Wheeler solenoid
    formula. Good to ~3 % for moderate cone angles, which matches the
    accuracy of the basic Wheeler formula on a straight solenoid.
    """
    r_avg = 0.5 * (radius_1_m + radius_2_m)
    return wheeler_solenoid_inductance(turns, r_avg, length_m)


def wire_length_for_secondary(turns: float, radius_1_m: float, radius_2_m: float) -> float:
    """Total length of wire wound on the secondary form.

    ``N · 2π · r_avg``; for a cone the radius varies linearly, so the
    average radius gives the mean turn length. The axial advance of the
    winding adds well under 0.01 % for close-wound coils and is neglected.
    """
    r_avg = 0.5 * (radius_1_m + radius_2_m)
    return turns * 2.0 * PI * r_avg


def copper_resistivity(temperature_c: float = DEFAULT_TEMP_C) -> float:
    """Resistivity of annealed copper at ``temperature_c`` (Ω·m)."""
    return COPPER_RESISTIVITY * (
        1.0 + COPPER_TEMP_COEFF * (temperature_c - COPPER_REFERENCE_TEMP_C)
    )


def dc_resistance(awg: int, length_m: float, temperature_c: float = DEFAULT_TEMP_C) -> float:
    """DC resistance of a length of magnet wire at temperature T."""
    temp_factor = copper_resistivity(temperature_c) / COPPER_RESISTIVITY
    return resistance_per_meter(awg) * length_m * temp_factor


def skin_depth(frequency_hz: float, temperature_c: float = DEFAULT_TEMP_C) -> float:
    """Skin depth in copper at the given frequency and temperature.

    δ = √(ρ(T) / (π · f · μ₀ · μᵣ))
    """
    if frequency_hz <= 0:
        return math.inf
    return math.sqrt(
        copper_resistivity(temperature_c) / (PI * frequency_hz * MU_0 * COPPER_PERMEABILITY)
    )


def ac_resistance(
    r_dc: float,
    wire_radius_m: float,
    frequency_hz: float,
    temperature_c: float = DEFAULT_TEMP_C,
) -> float:
    """AC resistance of an isolated round wire including skin effect.

    Exact Bessel-function solution for a round conductor of radius ``a``:

        R_ac / R_dc = Re[(q·a / 2) · J₀(q·a) / J₁(q·a)],   q = (1 − j) / δ

    which tends to 1 + (a/δ)⁴/48 at low frequency and to a/(2δ) + 1/4 at
    high frequency. The proximity effect of neighbouring turns is not
    included, so the result is a lower bound on the winding's real AC
    resistance (and the derived Q an upper bound).
    """
    delta = skin_depth(frequency_hz, temperature_c)
    x = wire_radius_m / delta
    if x < 1e-3:
        return r_dc
    qa = (1.0 - 1.0j) * x
    # jve is exponentially scaled; the scale factor cancels in the ratio.
    ratio = (0.5 * qa) * jve(0, qa) / jve(1, qa)
    return r_dc * float(ratio.real)


def calculate_secondary(inp: SecondaryInput) -> SecondaryOutput:
    """Compute every output for a secondary coil.

    Parameters
    ----------
    inp
        A :class:`SecondaryInput` model. All length fields are in meters.

    Returns
    -------
    SecondaryOutput
        Filled with inductance, self-capacitance, resonant frequency,
        wire length, resistances, Q factor, impedance, etc.
    """
    geometry = detect_secondary_geometry(inp.radius_1, inp.radius_2)
    winding_height = inp.height_2 - inp.height_1

    if geometry == CoilGeometry.SOLENOID:
        inductance = wheeler_solenoid_inductance(inp.turns, inp.radius_1, winding_height)
    else:
        inductance = conical_inductance(inp.turns, inp.radius_1, inp.radius_2, winding_height)

    # Self-capacitance via Medhurst, using the average diameter.
    avg_diameter = inp.radius_1 + inp.radius_2
    c_self = self_capacitance_farads(winding_height, avg_diameter)

    # Bare resonant frequency (no topload).
    f_res = resonant_frequency(inductance, c_self)

    wire_radius = 0.5 * bare_diameter_m(inp.wire_awg)
    wire_len = wire_length_for_secondary(inp.turns, inp.radius_1, inp.radius_2)

    r_dc = dc_resistance(inp.wire_awg, wire_len, inp.temperature_c)
    r_ac = ac_resistance(r_dc, wire_radius, f_res, inp.temperature_c)

    return SecondaryOutput(
        inductance_h=inductance,
        self_capacitance_f=c_self,
        resonant_frequency_hz=f_res,
        wire_length_m=wire_len,
        dc_resistance_ohms=r_dc,
        ac_resistance_ohms=r_ac,
        skin_depth_m=skin_depth(f_res, inp.temperature_c),
        q_factor=2.0 * PI * f_res * inductance / r_ac,
        impedance_ohms=characteristic_impedance(inductance, c_self),
        winding_height_m=winding_height,
        aspect_ratio=winding_height / avg_diameter,
        wire_spacing_m=winding_height / inp.turns,
        coil_geometry=geometry,
    )
