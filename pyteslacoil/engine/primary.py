"""Primary coil calculations.

Supports flat-spiral (pancake), helical, and conical primaries. Inductance
is computed with Wheeler's formulas for flat spirals and helices and with a
filamentary numerical sum for (inverse) conical windings.

References
----------
- H.A. Wheeler, "Simple Inductance Formulas for Radio Coils", Proc. IRE,
  16 (Oct 1928), pp. 1398-1400. Pancake formula appears in the same paper.
- F.W. Grover, "Inductance Calculations: Working Formulas and Tables"
  (Dover, 1946).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from pyteslacoil.constants import COPPER_RESISTIVITY, PI
from pyteslacoil.engine.inductance import (
    Filaments,
    filament_self_inductance,
    straight_wire_inductance,
    wheeler_pancake_inductance,
    wheeler_solenoid_inductance,
    winding_filaments,
)
from pyteslacoil.engine.resonance import characteristic_impedance, resonant_frequency
from pyteslacoil.models.enums import ConductorType, PrimaryGeometry
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput
from pyteslacoil.units import lengths_equal

__all__ = [
    "TUBE_WALL_FRACTION",
    "calculate_primary",
    "conductor_cross_section",
    "conical_primary_inductance",
    "detect_primary_geometry",
    "filamentary_coil_inductance",
    "lead_inductance",
    "primary_coil_inductance",
    "primary_dc_resistance",
    "primary_filaments",
    "primary_wire_length",
    "wheeler_helical_inductance",
    "wheeler_pancake_inductance",
]

TUBE_WALL_FRACTION: float = 0.05
"""Assumed wall thickness of copper tubing, as a fraction of its outer diameter."""

# A helical primary is a solenoid; the formula is shared with the secondary.
wheeler_helical_inductance = wheeler_solenoid_inductance


def detect_primary_geometry(inp: PrimaryInput) -> PrimaryGeometry:
    """Classify primary geometry from its height/radius extents."""
    if lengths_equal(inp.height_1, inp.height_2):
        return PrimaryGeometry.FLAT_SPIRAL
    if lengths_equal(inp.radius_1, inp.radius_2):
        return PrimaryGeometry.HELICAL
    if inp.radius_2 > inp.radius_1:
        return PrimaryGeometry.CONICAL
    return PrimaryGeometry.INVERSE_CONICAL


def primary_filaments(inp: PrimaryInput) -> Filaments:
    """The primary winding as weighted circular filaments (one per turn)."""
    return winding_filaments(inp.radius_1, inp.radius_2, inp.height_1, inp.height_2, inp.turns)


def filamentary_coil_inductance(
    radii_m: ArrayLike,
    heights_m: ArrayLike,
    wire_radius_m: float,
    weights: ArrayLike | None = None,
) -> float:
    """Inductance of a coil given as explicit circular filaments.

    Every filament contributes its self-inductance and its mutual inductance
    to every other filament (an O(N²) sum, vectorised with NumPy).
    ``weights`` (default 1) lets a filament stand for a fraction of a turn.
    """
    radii = np.asarray(radii_m, dtype=float)
    if radii.size == 0:
        return 0.0
    heights = np.asarray(heights_m, dtype=float)
    w = np.ones_like(radii) if weights is None else np.asarray(weights, dtype=float)
    return filament_self_inductance(Filaments(radii, heights, w), wire_radius_m)


def conical_primary_inductance(inp: PrimaryInput) -> float:
    """Inductance of a conical primary coil via the filament sum."""
    return filament_self_inductance(primary_filaments(inp), 0.5 * inp.wire_diameter)


def primary_coil_inductance(inp: PrimaryInput, geometry: PrimaryGeometry | None = None) -> float:
    """Inductance of the primary winding itself (excluding the leads)."""
    geometry = geometry or detect_primary_geometry(inp)
    if geometry == PrimaryGeometry.FLAT_SPIRAL:
        return wheeler_pancake_inductance(inp.turns, inp.radius_1, inp.radius_2)
    if geometry == PrimaryGeometry.HELICAL:
        return wheeler_helical_inductance(inp.turns, inp.radius_1, abs(inp.height_2 - inp.height_1))
    return conical_primary_inductance(inp)


def lead_inductance(lead_length_m: float, lead_diameter_m: float) -> float:
    """Inductance of the (straight) primary leads, see
    :func:`~pyteslacoil.engine.inductance.straight_wire_inductance`."""
    return straight_wire_inductance(lead_length_m, lead_diameter_m)


def primary_wire_length(inp: PrimaryInput) -> float:
    """Length of conductor wound on the primary form.

    The radius varies linearly along the winding, so every geometry has a
    mean turn length of ``2π · r_avg``; the pitch adds a negligible amount.
    """
    r_avg = 0.5 * (inp.radius_1 + inp.radius_2)
    return inp.turns * 2.0 * PI * r_avg


def conductor_cross_section(inp: PrimaryInput) -> float:
    """Conducting cross-section of the primary conductor (m²).

    Round wire: π·(d/2)². Ribbon: width · thickness. Tube: a thin-wall tube
    whose wall is :data:`TUBE_WALL_FRACTION` of the outer diameter.
    """
    if inp.conductor_type == ConductorType.RIBBON:
        if inp.ribbon_width is None or inp.ribbon_thickness is None:
            raise ValueError("A ribbon conductor requires ribbon_width and ribbon_thickness.")
        return inp.ribbon_width * inp.ribbon_thickness
    outer = 0.5 * inp.wire_diameter
    if inp.conductor_type == ConductorType.TUBE:
        inner = outer - TUBE_WALL_FRACTION * inp.wire_diameter
        return PI * (outer * outer - inner * inner)
    return PI * outer * outer


def primary_dc_resistance(length_m: float, inp: PrimaryInput) -> float:
    """DC resistance of ``length_m`` of the primary conductor, R = ρ · ℓ / A."""
    return COPPER_RESISTIVITY * length_m / conductor_cross_section(inp)


def calculate_primary(inp: PrimaryInput) -> PrimaryOutput:
    """Compute inductance, resonance and resistance of a primary coil."""
    geometry = detect_primary_geometry(inp)

    coil_l = primary_coil_inductance(inp, geometry)
    lead_l = lead_inductance(inp.lead_length, inp.lead_diameter)
    total_l = coil_l + lead_l

    wire_len = primary_wire_length(inp)

    return PrimaryOutput(
        inductance_h=coil_l,
        lead_inductance_h=lead_l,
        total_inductance_h=total_l,
        resonant_frequency_hz=resonant_frequency(total_l, inp.capacitance),
        impedance_ohms=characteristic_impedance(total_l, inp.capacitance),
        dc_resistance_ohms=primary_dc_resistance(wire_len, inp),
        wire_length_m=wire_len,
        primary_geometry=geometry,
    )
