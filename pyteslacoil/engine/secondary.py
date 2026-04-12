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
"""

from __future__ import annotations

import math

from pyteslacoil.constants import (
    COPPER_PERMEABILITY,
    COPPER_RESISTIVITY,
    COPPER_TEMP_COEFF,
    MU_0,
    PI,
)
from pyteslacoil.engine.medhurst import self_capacitance_pf
from pyteslacoil.models.coil_design import CoilGeometry
from pyteslacoil.models.secondary_model import SecondaryInput, SecondaryOutput
from pyteslacoil.wire_data import bare_diameter_m, resistance_per_meter


def _detect_geometry(radius_1: float, radius_2: float) -> CoilGeometry:
    """Classify the secondary coil from its top/bottom radii."""
    if math.isclose(radius_1, radius_2, rel_tol=1e-6):
        return CoilGeometry.SOLENOID
    if radius_2 > radius_1:
        return CoilGeometry.CONICAL
    return CoilGeometry.INVERSE_CONICAL


def wheeler_solenoid_inductance(
    turns: float, radius_m: float, length_m: float
) -> float:
    """Wheeler's classical formula for a single-layer solenoid.

    Returns inductance in Henries.

        L = (μ₀ · N² · π · r²) / (l + 0.9 · r)

    Accurate to ~1 % for typical Tesla coil aspect ratios (l/d ≥ 0.4).
    """
    if length_m <= 0 or radius_m <= 0 or turns <= 0:
        return 0.0
    return (MU_0 * turns * turns * PI * radius_m * radius_m) / (length_m + 0.9 * radius_m)


def conical_inductance(
    turns: float,
    radius_1_m: float,
    radius_2_m: float,
    length_m: float,
) -> float:
    """Inductance of a conical (or inverse conical) single-layer coil.

    Approximation: average the radii and reuse the Wheeler solenoid
    formula. Good to ~3 % for moderate cone angles, which matches the
    accuracy of the basic Wheeler formula on a straight solenoid. For high
    accuracy at extreme cone angles use the Neumann/filamentary mutual
    inductance method (see :mod:`pyteslacoil.engine.coupling`).
    """
    r_avg = 0.5 * (radius_1_m + radius_2_m)
    return wheeler_solenoid_inductance(turns, r_avg, length_m)


def wire_length_for_secondary(
    turns: float, radius_1_m: float, radius_2_m: float
) -> float:
    """Total length of wire wound on the secondary form.

    For a solenoid this is exactly ``N · 2π · r``. For a cone the average
    radius gives an exact answer for a uniform-pitch winding.
    """
    r_avg = 0.5 * (radius_1_m + radius_2_m)
    return turns * 2.0 * PI * r_avg


def dc_resistance(
    awg: int, length_m: float, temperature_c: float = 20.0
) -> float:
    """DC resistance of a length of magnet wire at temperature T."""
    r_per_m = resistance_per_meter(awg)
    temp_factor = 1.0 + COPPER_TEMP_COEFF * (temperature_c - 20.0)
    return r_per_m * length_m * temp_factor


def skin_depth(frequency_hz: float) -> float:
    """Skin depth in copper at the given frequency.

    δ = √(ρ / (π · f · μ₀ · μᵣ))
    """
    if frequency_hz <= 0:
        return float("inf")
    return math.sqrt(
        COPPER_RESISTIVITY / (PI * frequency_hz * MU_0 * COPPER_PERMEABILITY)
    )


def ac_resistance(
    r_dc: float, wire_radius_m: float, frequency_hz: float
) -> float:
    """AC resistance of a round wire including the skin-effect penalty.

    For a wire of radius ``a`` at frequency ``f`` with skin depth δ:

    - if ``a < 2δ`` the skin effect is small and ``R_ac ≈ R_dc``
    - otherwise ``R_ac ≈ R_dc · a / (2δ)``  (high-frequency approximation)
    """
    delta = skin_depth(frequency_hz)
    if wire_radius_m < 2.0 * delta:
        return r_dc
    return r_dc * wire_radius_m / (2.0 * delta)


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
    geometry = _detect_geometry(inp.radius_1, inp.radius_2)
    winding_height = inp.height_2 - inp.height_1

    # Inductance.
    if geometry == CoilGeometry.SOLENOID:
        L = wheeler_solenoid_inductance(inp.turns, inp.radius_1, winding_height)
    else:
        L = conical_inductance(
            inp.turns, inp.radius_1, inp.radius_2, winding_height
        )

    # Self-capacitance via Medhurst, using the average diameter.
    avg_diameter = inp.radius_1 + inp.radius_2
    c_self_pf = self_capacitance_pf(winding_height, avg_diameter)
    c_self_f = c_self_pf * 1e-12

    # Bare resonant frequency (no topload).
    if L > 0 and c_self_f > 0:
        f_res = 1.0 / (2.0 * PI * math.sqrt(L * c_self_f))
    else:
        f_res = 0.0

    # Wire geometry.
    wire_d = bare_diameter_m(inp.wire_awg)
    wire_radius = 0.5 * wire_d
    wire_len = wire_length_for_secondary(inp.turns, inp.radius_1, inp.radius_2)

    # DC and AC resistance.
    r_dc = dc_resistance(inp.wire_awg, wire_len, inp.temperature_c)
    r_ac = ac_resistance(r_dc, wire_radius, f_res)
    delta = skin_depth(f_res)

    # Q factor and impedance.
    if r_ac > 0 and L > 0 and f_res > 0:
        q = 2.0 * PI * f_res * L / r_ac
    else:
        q = 0.0
    if c_self_f > 0 and L > 0:
        impedance = math.sqrt(L / c_self_f)
    else:
        impedance = 0.0

    aspect_ratio = winding_height / (2.0 * 0.5 * (inp.radius_1 + inp.radius_2))
    wire_spacing = winding_height / inp.turns if inp.turns > 0 else 0.0

    return SecondaryOutput(
        inductance_h=L,
        inductance_uh=L * 1e6,
        inductance_mh=L * 1e3,
        self_capacitance_f=c_self_f,
        self_capacitance_pf=c_self_pf,
        resonant_frequency_hz=f_res,
        resonant_frequency_khz=f_res / 1000.0,
        wire_length_m=wire_len,
        wire_length_ft=wire_len / 0.3048,
        dc_resistance_ohms=r_dc,
        ac_resistance_ohms=r_ac,
        skin_depth_m=delta,
        q_factor=q,
        impedance_ohms=impedance,
        winding_height_m=winding_height,
        aspect_ratio=aspect_ratio,
        wire_spacing_m=wire_spacing,
        coil_geometry=geometry,
    )
