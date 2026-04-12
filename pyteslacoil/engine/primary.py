"""Primary coil calculations.

Supports flat-spiral (pancake), helical, and conical primaries. Inductance
is computed analytically where possible (Wheeler) and falls back to a
filamentary numerical sum for true conicals.

References
----------
- H.A. Wheeler, "Simple Inductance Formulas for Radio Coils", Proc. IRE,
  16 (Oct 1928), pp. 1398-1400. Pancake formula appears in the same paper.
- F.W. Grover, "Inductance Calculations: Working Formulas and Tables"
  (Dover, 1946).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import ellipe, ellipk

from pyteslacoil.constants import COPPER_RESISTIVITY, MU_0, PI
from pyteslacoil.models.coil_design import ConductorType, PrimaryGeometry
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput


def _detect_primary_geometry(inp: PrimaryInput) -> PrimaryGeometry:
    """Classify primary geometry from height/radius extents."""
    flat = math.isclose(inp.height_1, inp.height_2, abs_tol=1e-9)
    same_radius = math.isclose(inp.radius_1, inp.radius_2, abs_tol=1e-9)

    if flat and not same_radius:
        return PrimaryGeometry.FLAT_SPIRAL
    if same_radius and not flat:
        return PrimaryGeometry.HELICAL
    if not flat and not same_radius:
        return (
            PrimaryGeometry.CONICAL
            if inp.radius_2 > inp.radius_1
            else PrimaryGeometry.INVERSE_CONICAL
        )
    # both equal -> degenerate; treat as helical with zero length, which
    # gives an effectively zero inductance and lets the UI report it.
    return PrimaryGeometry.HELICAL


def wheeler_pancake_inductance(
    turns: float, r_inner_m: float, r_outer_m: float
) -> float:
    """Wheeler's flat spiral (pancake) inductance.

        L_uH = r_avg² · N² / (8·r_avg + 11·w)   [r_avg, w in inches]

    The SI form below is dimensionally consistent and returns Henries.
    """
    if turns <= 0 or r_outer_m <= r_inner_m:
        return 0.0
    r_avg = 0.5 * (r_inner_m + r_outer_m)
    w = r_outer_m - r_inner_m
    # SI version using μ₀.  See Wheeler (1928) eqn. for flat coils.
    return (MU_0 * turns * turns * r_avg * r_avg) / (8.0 * r_avg + 11.0 * w)


def wheeler_helical_inductance(
    turns: float, radius_m: float, length_m: float
) -> float:
    if length_m <= 0 or radius_m <= 0 or turns <= 0:
        return 0.0
    return (MU_0 * turns * turns * PI * radius_m * radius_m) / (length_m + 0.9 * radius_m)


def _filament_self_inductance(radius_m: float, wire_radius_m: float) -> float:
    """Self-inductance of a single circular loop of wire."""
    if radius_m <= 0 or wire_radius_m <= 0:
        return 0.0
    return (
        MU_0
        * radius_m
        * (math.log(8.0 * radius_m / wire_radius_m) - 2.0 + 0.25)
    )


def _filament_mutual(r1: float, r2: float, d: float) -> float:
    """Mutual inductance between two coaxial circular filaments.

    Uses scipy's elliptic integrals K and E.
    """
    if r1 <= 0 or r2 <= 0:
        return 0.0
    k_sq = 4.0 * r1 * r2 / ((r1 + r2) ** 2 + d * d)
    # Clamp tiny floating-point overshoot.
    k_sq = min(max(k_sq, 0.0), 1.0 - 1e-15)
    k = math.sqrt(k_sq)
    K = ellipk(k_sq)
    E = ellipe(k_sq)
    return MU_0 * math.sqrt(r1 * r2) * ((2.0 / k - k) * K - (2.0 / k) * E)


def filamentary_coil_inductance(
    radii_m: np.ndarray, heights_m: np.ndarray, wire_radius_m: float
) -> float:
    """Inductance of an arbitrary coil discretized as N circular filaments.

    For each turn we compute its self-inductance plus the mutual to every
    other turn. This is O(N²) but exact (subject to filament idealization).
    """
    n = len(radii_m)
    if n == 0:
        return 0.0
    L = 0.0
    for i in range(n):
        L += _filament_self_inductance(radii_m[i], wire_radius_m)
        for j in range(i + 1, n):
            d = abs(heights_m[j] - heights_m[i])
            L += 2.0 * _filament_mutual(radii_m[i], radii_m[j], d)
    return L


def conical_primary_inductance(inp: PrimaryInput) -> float:
    """Inductance of a conical primary coil via filament sum."""
    n = max(1, int(round(inp.turns)))
    radii = np.linspace(inp.radius_1, inp.radius_2, n)
    heights = np.linspace(inp.height_1, inp.height_2, n)
    return filamentary_coil_inductance(radii, heights, 0.5 * inp.wire_diameter)


def lead_inductance(lead_length_m: float, lead_diameter_m: float) -> float:
    """Inductance of a single straight wire (lead).

        L ≈ (μ₀ · ℓ / 2π) · (ln(2ℓ / r) − 1)

    Reference: Grover (1946), Eq. 7-1.
    """
    if lead_length_m <= 0 or lead_diameter_m <= 0:
        return 0.0
    r = 0.5 * lead_diameter_m
    return (
        (MU_0 * lead_length_m / (2.0 * PI))
        * (math.log(2.0 * lead_length_m / r) - 1.0)
    )


def primary_wire_length(inp: PrimaryInput, geometry: PrimaryGeometry) -> float:
    """Length of conductor wound on the primary form."""
    if geometry == PrimaryGeometry.FLAT_SPIRAL:
        # Average radius times circumference per turn.
        r_avg = 0.5 * (inp.radius_1 + inp.radius_2)
        return inp.turns * 2.0 * PI * r_avg
    if geometry == PrimaryGeometry.HELICAL:
        return inp.turns * 2.0 * PI * inp.radius_1
    # conical / inverse conical
    r_avg = 0.5 * (inp.radius_1 + inp.radius_2)
    return inp.turns * 2.0 * PI * r_avg


def primary_dc_resistance(
    length_m: float, conductor_type: ConductorType, inp: PrimaryInput
) -> float:
    """DC resistance of the primary conductor.

    For round conductors: R = ρ · ℓ / A where A = π · (d/2)².
    For ribbon: A = width · thickness.  Tube: thin-wall area.
    """
    if length_m <= 0:
        return 0.0
    if conductor_type == ConductorType.ROUND:
        radius = 0.5 * inp.wire_diameter
        area = PI * radius * radius
    elif conductor_type == ConductorType.RIBBON:
        if not inp.ribbon_width or not inp.ribbon_thickness:
            return 0.0
        area = inp.ribbon_width * inp.ribbon_thickness
    elif conductor_type == ConductorType.TUBE:
        # Treat as a thin-wall tube of nominal wall thickness 0.05·d.
        outer = 0.5 * inp.wire_diameter
        wall = 0.05 * inp.wire_diameter
        inner = max(outer - wall, 0.0)
        area = PI * (outer * outer - inner * inner)
    else:
        area = PI * (0.5 * inp.wire_diameter) ** 2
    return COPPER_RESISTIVITY * length_m / area


def calculate_primary(inp: PrimaryInput) -> PrimaryOutput:
    geometry = _detect_primary_geometry(inp)

    if geometry == PrimaryGeometry.FLAT_SPIRAL:
        L = wheeler_pancake_inductance(inp.turns, inp.radius_1, inp.radius_2)
    elif geometry == PrimaryGeometry.HELICAL:
        L = wheeler_helical_inductance(
            inp.turns, inp.radius_1, abs(inp.height_2 - inp.height_1)
        )
    else:
        L = conical_primary_inductance(inp)

    L_lead = lead_inductance(inp.lead_length, inp.lead_diameter)
    L_total = L + L_lead

    if L_total > 0 and inp.capacitance > 0:
        f_res = 1.0 / (2.0 * PI * math.sqrt(L_total * inp.capacitance))
    else:
        f_res = 0.0

    if inp.capacitance > 0 and L_total > 0:
        impedance = math.sqrt(L_total / inp.capacitance)
    else:
        impedance = 0.0

    wire_len = primary_wire_length(inp, geometry)
    r_dc = primary_dc_resistance(wire_len, inp.conductor_type, inp)

    return PrimaryOutput(
        inductance_h=L,
        inductance_uh=L * 1e6,
        lead_inductance_h=L_lead,
        lead_inductance_uh=L_lead * 1e6,
        total_inductance_h=L_total,
        total_inductance_uh=L_total * 1e6,
        resonant_frequency_hz=f_res,
        resonant_frequency_khz=f_res / 1000.0,
        impedance_ohms=impedance,
        dc_resistance_ohms=r_dc,
        wire_length_m=wire_len,
        wire_length_ft=wire_len / 0.3048,
        primary_geometry=geometry,
    )
