"""Surrounding environment effects (ground plane, walls, ceiling).

A topload near grounded surfaces has a higher capacitance than in free space
because the surfaces carry induced (image) charges of the opposite sign.
This module estimates the effect to first order:

- the topload is replaced by a sphere with the same free-space capacitance,
  i.e. radius ``a = C₀ / (4π ε₀)``, centred at the topload height ``h``;
- each grounded surface lowers the topload potential by ``κ / d`` (in units
  of ``Q / 4π ε₀``), where ``d`` is its distance from the topload centre;
- so ``C = C₀ / (1 − a · Σ κᵢ / dᵢ)``.

Coefficients: a plane has ``κ = ½`` (one image charge at ``2d``); the walls,
a grounded cylinder of radius ``d`` around the coil axis, have
``κ ≈ 0.871`` (exact for a charge on the axis of an infinite cylinder). A
ground plane of finite radius ``R_g`` is weighted by the share of the
induced charge an infinite plane would carry within ``R_g``,
``1 − h / √(h² + R_g²)``. Interactions between surfaces (e.g. the image
series between floor and ceiling) are neglected, so treat the result as an
estimate; serious users should consult Paul Nicholson's TSSP / GEOTC.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import EPSILON_0, PI
from pyteslacoil.models.environment_model import EnvironmentInput, EnvironmentOutput

PLANE_IMAGE_COEFFICIENT: float = 0.5
WALL_IMAGE_COEFFICIENT: float = 0.8707
"""(2/π)∫₀^∞ K₀(u)/I₀(u) du — induced potential on the axis of a grounded cylinder."""

MAX_POTENTIAL_REDUCTION: float = 0.5
"""Cap on ``a · Σ κ/d``; beyond it the first-order model is not meaningful."""


def equivalent_sphere_radius(capacitance_f: float) -> float:
    """Radius of the isolated sphere with the given capacitance, ``C / (4π ε₀)``."""
    return capacitance_f / (4.0 * PI * EPSILON_0)


def _surface_terms(
    env: EnvironmentInput, height_m: float, radius_m: float
) -> tuple[list[tuple[str, float]], list[str]]:
    """``(label, κ/d)`` for every surface present, plus warnings for ignored ones."""
    terms: list[tuple[str, float]] = []
    warnings: list[str] = []
    if env.ground_plane_radius > 0:
        share = 1.0 - height_m / math.hypot(height_m, env.ground_plane_radius)
        label = f"Ground plane (radius {env.ground_plane_radius:.2f} m)"
        terms.append((label, share * PLANE_IMAGE_COEFFICIENT / height_m))
    if env.wall_radius > 0:
        if env.wall_radius <= radius_m:
            warnings.append("The wall radius is inside the topload; the walls were ignored.")
        else:
            label = f"Walls at radius {env.wall_radius:.2f} m"
            terms.append((label, WALL_IMAGE_COEFFICIENT / env.wall_radius))
    if env.ceiling_height > 0:
        clearance = env.ceiling_height - height_m
        if clearance <= radius_m:
            warnings.append("The ceiling is below the top of the topload; the ceiling was ignored.")
        else:
            label = f"Ceiling at {env.ceiling_height:.2f} m"
            terms.append((label, PLANE_IMAGE_COEFFICIENT / clearance))
    return terms, warnings


def _increase_percent(reduction: float) -> float:
    """Capacitance increase (%) for a relative potential reduction."""
    return 100.0 * (1.0 / (1.0 - min(reduction, MAX_POTENTIAL_REDUCTION)) - 1.0)


def proximity_factor(
    env: EnvironmentInput, topload_height_m: float, topload_capacitance_f: float
) -> float:
    """Multiplicative correction for the free-space topload capacitance."""
    out = calculate_environment(env, topload_height_m, topload_capacitance_f)
    return out.proximity_correction_factor


def calculate_environment(
    env: EnvironmentInput,
    topload_height_m: float | None = None,
    topload_capacitance_f: float | None = None,
) -> EnvironmentOutput:
    """Proximity correction for a topload at ``topload_height_m``.

    Without a topload (no height or zero capacitance) there is nothing to
    correct and the factor is 1.
    """
    present = env.ground_plane_radius > 0 or env.wall_radius > 0 or env.ceiling_height > 0
    if not present:
        return EnvironmentOutput(
            proximity_correction_factor=1.0, notes="Free space (no proximity effects)"
        )
    if not topload_height_m or not topload_capacitance_f:
        return EnvironmentOutput(
            proximity_correction_factor=1.0, notes="No topload to correct for proximity effects"
        )

    a = equivalent_sphere_radius(topload_capacitance_f)
    terms, warnings = _surface_terms(env, topload_height_m, a)
    notes = [f"{label}: +{_increase_percent(a * t):.1f} %" for label, t in terms]

    reduction = a * sum(t for _, t in terms)
    if reduction > MAX_POTENTIAL_REDUCTION:
        warnings.append(
            "The topload is too close to grounded surfaces for the proximity model; "
            "the correction was capped."
        )
        reduction = MAX_POTENTIAL_REDUCTION
    return EnvironmentOutput(
        proximity_correction_factor=1.0 / (1.0 - reduction),
        notes="; ".join(notes) if notes else "No surfaces close enough to matter",
        warnings=warnings,
    )
