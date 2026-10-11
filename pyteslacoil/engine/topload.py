"""Topload (toroid / sphere) capacitance calculations.

The topload provides the bulk of the secondary's terminal capacitance and
sets where the streamers break out. Both shapes are computed as *isolated*
conductors in free space; nearby grounded surfaces (floor, walls, ceiling)
are accounted for separately by :mod:`pyteslacoil.engine.environment`.

- Sphere: ``C = 4π ε₀ r`` (exact).
- Toroid: the exact solution in toroidal coordinates,

      C = 8 ε₀ c · Σₙ εₙ Q_{n−½}(cosh η₀) / P_{n−½}(cosh η₀)

  where ``R`` and ``a`` are the tube's centre-line and tube radii,
  ``cosh η₀ = R/a``, ``c = √(R² − a²)``, ``ε₀ = 1`` and ``εₙ = 2`` for
  ``n ≥ 1``, and P, Q are Legendre functions of half-integer degree
  (toroidal harmonics). The popular empirical fit
  ``2.8 · (1.2781 − d/D) · √(π (D − d) d / 4)`` pF (inches) agrees with it to
  ±2 % for ``d/D ≈ 0.15–0.3`` but is off by 7–20 % for thinner or fatter
  toroids, so the exact series is used instead.

References
----------
- W.R. Smythe, "Static and Dynamic Electricity" (3rd ed., McGraw-Hill,
  1968) — sphere and toroid solutions.
- V. Belevitch and J. Boersma, "Some electrical problems for a torus",
  Philips J. Res. 38 (1983), pp. 79-137.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.special import roots_legendre

from pyteslacoil.constants import EPSILON_0, PI
from pyteslacoil.engine._checks import require_positive
from pyteslacoil.models.enums import ToploadType
from pyteslacoil.models.topload_model import ToploadInput, ToploadOutput

# Gauss-Legendre nodes for the Laplace integral of P_{n-1/2} over [0, π].
_GL_X, _GL_W = roots_legendre(64)
_PHI = 0.5 * PI * (_GL_X + 1.0)
_PHI_W = 0.5 * PI * _GL_W

_SERIES_RTOL = 1e-10
_SERIES_MAX_TERMS = 4000


def calculate_sphere_capacitance(diameter_m: float) -> float:
    """Capacitance of an isolated sphere in vacuum.

        C = 4·π·ε₀·r

    Returns capacitance in farads.
    """
    require_positive(diameter_m=diameter_m)
    return 4.0 * PI * EPSILON_0 * (0.5 * diameter_m)


def _legendre_p_half(n: int, base: np.ndarray) -> float:
    """P_{n−½}(z) for z > 1 via Laplace's integral (1/π)∫₀^π (z + √(z²−1) cos φ)^(n−½) dφ.

    ``base`` is ``z + √(z²−1) cos φ`` evaluated at the quadrature nodes.
    """
    return float(np.dot(_PHI_W, base ** (n - 0.5))) / PI


def _legendre_q_half(n: int, z: float, s: float) -> float:
    """Q_{n−½}(z) for z > 1 via Heine's integral ∫₀^∞ (z + √(z²−1) cosh t)^(−n−½) dt."""
    exponent = n + 0.5
    # Beyond t_max the integrand is below e^-50 of its peak.
    t_max = 50.0 / exponent + 2.0 * math.log(2.0 / s + 2.0)
    value, _ = quad(
        lambda t: (z + s * math.cosh(t)) ** (-exponent),
        0.0,
        t_max,
        limit=200,
        epsabs=0.0,
        epsrel=1e-12,
    )
    return value


def torus_capacitance(centre_radius_m: float, tube_radius_m: float) -> float:
    """Exact capacitance of an isolated ring torus (farads).

    ``centre_radius_m`` is the radius of the tube's centre line (R) and
    ``tube_radius_m`` the tube radius (a); requires R > a > 0.
    """
    require_positive(tube_radius_m=tube_radius_m)
    if centre_radius_m <= tube_radius_m:
        raise ValueError("A ring torus needs centre_radius_m > tube_radius_m")
    z = centre_radius_m / tube_radius_m
    s = math.sqrt(z * z - 1.0)
    base = z + s * np.cos(_PHI)  # strictly positive on [0, π]

    total = 0.0
    prev = term = 0.0
    for n in range(_SERIES_MAX_TERMS):
        weight = 1.0 if n == 0 else 2.0
        prev, term = term, weight * _legendre_q_half(n, z, s) / _legendre_p_half(n, base)
        total += term
        if n >= 2 and term < _SERIES_RTOL * total:
            break
    else:
        # Very fat tori converge slowly; the terms decay geometrically, so add the tail.
        ratio = term / prev if prev > 0 else 0.0
        if 0.0 < ratio < 1.0:
            total += term * ratio / (1.0 - ratio)
    return 8.0 * EPSILON_0 * tube_radius_m * s * total


def calculate_toroid_capacitance(major_diameter_m: float, minor_diameter_m: float) -> float:
    """Capacitance of an isolated toroid (farads).

    ``major_diameter_m`` is the overall outer diameter D and
    ``minor_diameter_m`` the tube diameter d; requires d < D/2 so the
    toroid has a centre hole.
    """
    require_positive(major_diameter_m=major_diameter_m, minor_diameter_m=minor_diameter_m)
    if 2.0 * minor_diameter_m >= major_diameter_m:
        raise ValueError("minor_diameter must be less than half the major_diameter")
    centre_radius = 0.5 * (major_diameter_m - minor_diameter_m)
    return torus_capacitance(centre_radius, 0.5 * minor_diameter_m)


def calculate_topload(inp: ToploadInput) -> ToploadOutput:
    """Free-space capacitance of the configured topload."""
    if inp.topload_type == ToploadType.NONE:
        c = 0.0
    elif inp.topload_type == ToploadType.SPHERE:
        if inp.sphere_diameter is None:
            raise ValueError("Sphere topload requires sphere_diameter.")
        c = calculate_sphere_capacitance(inp.sphere_diameter)
    elif inp.topload_type == ToploadType.TOROID:
        if inp.major_diameter is None or inp.minor_diameter is None:
            raise ValueError("Toroid topload requires major_diameter and minor_diameter.")
        c = calculate_toroid_capacitance(inp.major_diameter, inp.minor_diameter)
    else:  # pragma: no cover - exhaustive over ToploadType
        raise ValueError(f"Unknown topload type: {inp.topload_type!r}")
    return ToploadOutput(capacitance_f=c, topload_type=inp.topload_type)


def stack_capacitance(toploads: list[ToploadInput]) -> float:
    """Rough upper bound for several stacked toploads: their capacitances summed.

    Closely stacked toploads shield each other, so the real total is
    noticeably lower than this parallel sum; use a field solver for stacks.
    """
    return sum(calculate_topload(t).capacitance_f for t in toploads)
