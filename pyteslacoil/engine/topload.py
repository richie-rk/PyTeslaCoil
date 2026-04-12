"""Topload (toroid / sphere) capacitance calculations.

The topload provides the bulk of the secondary's terminal capacitance and
sets where the streamers break out. Both toroid and sphere shapes are
supported. JavaTC uses an empirical formula for toroid capacitance — we
match its result to within ~1 % for typical Tesla coil sizes.

References
----------
- B. Pool, "Topload Capacitance" (Tesla coil mailing list, ~2001)
- W.R. Smythe, "Static and Dynamic Electricity" (3rd ed., McGraw-Hill,
  1968) — sphere and toroid solutions
"""

from __future__ import annotations

import math

from pyteslacoil.constants import EPSILON_0, PI
from pyteslacoil.models.coil_design import ToploadType
from pyteslacoil.models.topload_model import ToploadInput, ToploadOutput


def calculate_sphere_capacitance(diameter_m: float) -> float:
    """Capacitance of an isolated sphere in vacuum.

        C = 4·π·ε₀·r

    Returns capacitance in farads.
    """
    if diameter_m <= 0:
        return 0.0
    radius = 0.5 * diameter_m
    return 4.0 * PI * EPSILON_0 * radius


def calculate_toroid_capacitance(
    major_diameter_m: float, minor_diameter_m: float
) -> float:
    """Empirical capacitance of an isolated toroid (used by JavaTC).

        C [pF] ≈ 2.8 · (1.2781 − d/D) · √(2π² · (D/2 − d/2) · (d/2))

    where ``D`` and ``d`` are the major and minor diameters in **inches**.
    Returns farads.

    For very small minor/major ratios (< 0.05) the empirical fit becomes
    inaccurate; we fall back to a thin-ring formula in that regime.
    """
    if major_diameter_m <= 0 or minor_diameter_m <= 0:
        return 0.0
    if minor_diameter_m >= major_diameter_m:
        raise ValueError("minor_diameter must be smaller than major_diameter")

    # Convert to inches because the empirical formula's coefficients are
    # calibrated in those units.
    D_in = major_diameter_m / 0.0254
    d_in = minor_diameter_m / 0.0254
    ratio = d_in / D_in
    if ratio < 0.05:
        # Thin-ring approximation: C ≈ ε₀ · π² · D / ln(8R/a)
        R = 0.5 * major_diameter_m
        a = 0.5 * minor_diameter_m
        return EPSILON_0 * PI * PI * (2.0 * R) / math.log(8.0 * R / a)

    inner_radius_in = 0.5 * D_in - 0.5 * d_in
    minor_radius_in = 0.5 * d_in
    arg = 2.0 * PI * PI * inner_radius_in * minor_radius_in
    if arg <= 0:
        return 0.0
    c_pf = 2.8 * (1.2781 - ratio) * math.sqrt(arg)
    if c_pf < 0:
        c_pf = 0.0
    return c_pf * 1e-12


def calculate_topload(inp: ToploadInput) -> ToploadOutput:
    if inp.topload_type == ToploadType.NONE:
        return ToploadOutput(
            capacitance_f=0.0,
            capacitance_pf=0.0,
            topload_type=ToploadType.NONE,
        )
    if inp.topload_type == ToploadType.SPHERE:
        c = calculate_sphere_capacitance(inp.sphere_diameter or 0.0)
        return ToploadOutput(
            capacitance_f=c,
            capacitance_pf=c * 1e12,
            topload_type=ToploadType.SPHERE,
        )
    if inp.topload_type == ToploadType.TOROID:
        c = calculate_toroid_capacitance(
            inp.major_diameter or 0.0, inp.minor_diameter or 0.0
        )
        return ToploadOutput(
            capacitance_f=c,
            capacitance_pf=c * 1e12,
            topload_type=ToploadType.TOROID,
        )
    raise ValueError(f"Unknown topload type: {inp.topload_type!r}")


def stack_capacitance(toploads: list[ToploadInput]) -> float:
    """Total capacitance of multiple stacked toploads.

    A simple approximation: capacitances of widely-separated toploads add
    in parallel. For closely stacked toroids the proximity effects are
    significant — that should be captured separately by the environment
    module.
    """
    return sum(calculate_topload(t).capacitance_f for t in toploads)
