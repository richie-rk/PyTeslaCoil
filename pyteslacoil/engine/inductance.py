"""Inductance formulas shared by the primary, secondary and coupling modules.

All lengths are in meters and all inductances in henries.

References
----------
- H.A. Wheeler, "Simple Inductance Formulas for Radio Coils", Proc. IRE,
  16 (Oct 1928), pp. 1398-1400.
- J.C. Maxwell, "A Treatise on Electricity and Magnetism" (1873) — mutual
  inductance of two coaxial circles via complete elliptic integrals.
- F.W. Grover, "Inductance Calculations: Working Formulas and Tables"
  (Dover, 1946).
"""

from __future__ import annotations

import math
from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import ellipe, ellipk

from pyteslacoil.constants import MU_0, PI
from pyteslacoil.engine._checks import require_positive

# Wheeler's formulas are usually quoted in inches and microhenries:
#
#     solenoid      L[µH] = r² N² / (9 r + 10 l)
#     flat spiral   L[µH] = r² N² / (8 r + 11 w)
#
# The implicit constant (0.1 µH per inch) equals 10·π·µ₀ per meter to 0.3 %,
# so the SI forms below are  L[H] = 10·π·µ₀ · r² N² / (9 r + 10 l)  etc.,
# i.e. the solenoid formula is exactly µ₀·π·N²·r² / (l + 0.9 r).
_WHEELER_K = 10.0 * PI * MU_0


def wheeler_solenoid_inductance(turns: float, radius_m: float, length_m: float) -> float:
    """Wheeler's single-layer solenoid formula.

        L = µ₀ · π · N² · r² / (l + 0.9 · r)

    Accurate to ~1 % for l/d ≥ 0.4, which covers Tesla coil secondaries and
    helical primaries.
    """
    require_positive(turns=turns, radius_m=radius_m, length_m=length_m)
    return _WHEELER_K * turns * turns * radius_m * radius_m / (9.0 * radius_m + 10.0 * length_m)


def wheeler_pancake_inductance(turns: float, r_inner_m: float, r_outer_m: float) -> float:
    """Wheeler's flat-spiral (pancake) formula.

        L = 10 · π · µ₀ · N² · r² / (8 · r + 11 · w)

    with ``r`` the mean radius and ``w`` the radial width of the winding
    (Wheeler's ``L[µH] = r² N² / (8 r + 11 w)`` with r, w in inches). The
    order of the two radii does not matter.
    """
    r_in, r_out = sorted((r_inner_m, r_outer_m))
    require_positive(turns=turns, width_m=r_out - r_in)
    if r_in < 0:
        raise ValueError(f"radii must not be negative, got {r_inner_m!r}, {r_outer_m!r}")
    r_avg = 0.5 * (r_in + r_out)
    width = r_out - r_in
    return _WHEELER_K * turns * turns * r_avg * r_avg / (8.0 * r_avg + 11.0 * width)


def straight_wire_inductance(length_m: float, diameter_m: float) -> float:
    """High-frequency inductance of a straight round wire (Grover, Eq. 7-1).

        L ≈ (µ₀ · ℓ / 2π) · (ln(2ℓ / r) − 1)

    The formula assumes ℓ ≫ r; wires so short that it would turn negative
    return 0.
    """
    if length_m < 0:
        raise ValueError(f"length_m must not be negative, got {length_m!r}")
    require_positive(diameter_m=diameter_m)
    if length_m == 0:
        return 0.0
    r = 0.5 * diameter_m
    return max(0.0, (MU_0 * length_m / (2.0 * PI)) * (math.log(2.0 * length_m / r) - 1.0))


def loop_self_inductance(radius_m: ArrayLike, wire_radius_m: float) -> NDArray[np.float64]:
    """High-frequency self-inductance of a circular loop of round wire.

        L = µ₀ · R · (ln(8 R / a) − 2)

    At radio frequencies skin effect removes the internal inductance (the
    low-frequency formula has −7/4 instead of −2). Negative results, which
    only occur for loops smaller than the wire, are clamped to zero.
    """
    require_positive(wire_radius_m=wire_radius_m)
    radius = np.asarray(radius_m, dtype=float)
    return np.maximum(0.0, MU_0 * radius * (np.log(8.0 * radius / wire_radius_m) - 2.0))


def loop_mutual_inductance(
    r1: ArrayLike, z1: ArrayLike, r2: ArrayLike, z2: ArrayLike
) -> NDArray[np.float64]:
    """Mutual inductance between coaxial circular filaments (Maxwell).

        M = µ₀ √(r₁ r₂) · ((2/k − k) K(k²) − (2/k) E(k²)),
        k² = 4 r₁ r₂ / ((r₁ + r₂)² + (z₁ − z₂)²)

    The arguments broadcast against each other like NumPy arrays.
    """
    r1, z1, r2, z2 = (np.asarray(v, dtype=float) for v in (r1, z1, r2, z2))
    m = 4.0 * r1 * r2 / ((r1 + r2) ** 2 + (z1 - z2) ** 2)
    # Coincident filaments would make the integral diverge; clamp just below 1.
    m = np.clip(m, 0.0, 1.0 - 1e-15)
    k = np.sqrt(m)
    return MU_0 * np.sqrt(r1 * r2) * ((2.0 / k - k) * ellipk(m) - (2.0 / k) * ellipe(m))


class Filaments(NamedTuple):
    """A winding discretised into weighted coaxial circular filaments."""

    radii: NDArray[np.float64]
    heights: NDArray[np.float64]
    weights: NDArray[np.float64]


def winding_filaments(
    radius_start: float,
    radius_end: float,
    height_start: float,
    height_end: float,
    turns: float,
) -> Filaments:
    """Discretise a single-layer winding into one filament per turn.

    The conductor advances uniformly from ``(radius_start, height_start)`` to
    ``(radius_end, height_end)`` over ``turns`` turns. Each complete turn is
    represented by a loop at the turn's mid-point; a final partial turn of
    fraction ``f`` is a loop at its own mid-point with weight ``f``. The sum of
    the weights equals ``turns``, which keeps every inductance continuous in
    the (possibly fractional) turn count.
    """
    require_positive(turns=turns)
    n_full = math.floor(turns + 1e-9)
    frac = turns - n_full
    centres = np.arange(n_full, dtype=float) + 0.5
    weights = np.ones(n_full)
    if frac > 1e-9:
        centres = np.append(centres, n_full + 0.5 * frac)
        weights = np.append(weights, frac)
    t = centres / turns
    radii = radius_start + (radius_end - radius_start) * t
    heights = height_start + (height_end - height_start) * t
    return Filaments(radii, heights, weights)


def filament_mutual_inductance(a: Filaments, b: Filaments, dz: float = 0.0) -> float:
    """Total mutual inductance between two windings; ``dz`` shifts ``a`` upwards."""
    m = loop_mutual_inductance(
        a.radii[:, None], a.heights[:, None] + dz, b.radii[None, :], b.heights[None, :]
    )
    return float(a.weights @ m @ b.weights)


def filament_self_inductance(f: Filaments, wire_radius_m: float) -> float:
    """Self-inductance of a winding: loop self terms plus every pairwise mutual."""
    m = loop_mutual_inductance(
        f.radii[:, None], f.heights[:, None], f.radii[None, :], f.heights[None, :]
    )
    np.fill_diagonal(m, loop_self_inductance(f.radii, wire_radius_m))
    return float(f.weights @ m @ f.weights)
