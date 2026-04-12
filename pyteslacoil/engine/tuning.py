"""Auto-tune: find the primary turns count that matches the secondary.

The primary tank circuit is tuned by adjusting the number of turns. Given
the secondary resonant frequency, we solve for the primary turns ``N`` such
that

    f_pri(N) = 1 / (2π · √(L_pri(N) · C_tank))  ==  f_secondary

For a flat spiral the inductance is

    L = (μ₀ · N² · r_avg²) / (8 · r_avg + 11 · w)
    where w = N · pitch

so increasing N increases ``w`` as well — this is non-linear and is solved
with :func:`scipy.optimize.brentq`.
"""

from __future__ import annotations

import math
from typing import Tuple

from scipy.optimize import brentq

from pyteslacoil.constants import PI
from pyteslacoil.engine.primary import (
    calculate_primary,
    wheeler_helical_inductance,
    wheeler_pancake_inductance,
)
from pyteslacoil.models.coil_design import PrimaryGeometry
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput


def required_primary_inductance(target_frequency_hz: float, c_tank: float) -> float:
    """The primary inductance required to resonate at ``target_frequency_hz``.

        L = 1 / ((2π · f)² · C)
    """
    if target_frequency_hz <= 0 or c_tank <= 0:
        return 0.0
    omega = 2.0 * PI * target_frequency_hz
    return 1.0 / (omega * omega * c_tank)


def _flat_spiral_pitch(inp: PrimaryInput) -> float:
    if inp.turns <= 0:
        return inp.wire_diameter
    pitch = (inp.radius_2 - inp.radius_1) / inp.turns
    if pitch <= 0:
        pitch = inp.wire_diameter
    return pitch


def _helical_pitch(inp: PrimaryInput) -> float:
    if inp.turns <= 0:
        return inp.wire_diameter
    pitch = abs(inp.height_2 - inp.height_1) / inp.turns
    if pitch <= 0:
        pitch = inp.wire_diameter
    return pitch


def auto_tune(secondary_frequency_hz: float, primary: PrimaryInput) -> float:
    """Compute the (fractional) primary turn count that matches the secondary.

    Parameters
    ----------
    secondary_frequency_hz
        Target secondary resonant frequency.
    primary
        The primary input — only its geometry, capacitance and pitch are
        used. The ``turns`` field of ``primary`` is the *current* value
        and is overwritten by the result.

    Returns
    -------
    float
        The primary turns count (can be fractional, e.g. ``10.832``).
    """
    if secondary_frequency_hz <= 0 or primary.capacitance <= 0:
        return primary.turns

    L_target = required_primary_inductance(
        secondary_frequency_hz, primary.capacitance
    )

    # Geometry detection follows the same logic as the primary module.
    flat = math.isclose(primary.height_1, primary.height_2, abs_tol=1e-9)
    same_radius = math.isclose(primary.radius_1, primary.radius_2, abs_tol=1e-9)

    if flat and not same_radius:
        # Flat spiral: w = N * pitch (radial), r_avg = r1 + w/2
        pitch = _flat_spiral_pitch(primary)

        def residual(n: float) -> float:
            w = n * pitch
            r_outer = primary.radius_1 + w
            L = wheeler_pancake_inductance(n, primary.radius_1, r_outer)
            return L - L_target

    elif same_radius and not flat:
        # Helical: l = N * axial_pitch
        pitch = _helical_pitch(primary)

        def residual(n: float) -> float:
            length = n * pitch
            L = wheeler_helical_inductance(n, primary.radius_1, length)
            return L - L_target

    else:
        # Conical or degenerate: scale current geometry by the turns ratio
        # and use the full primary calculator. We assume L scales roughly
        # with N² for small adjustments around the current value.
        baseline = calculate_primary(primary).inductance_h
        if baseline <= 0:
            return primary.turns
        ratio = math.sqrt(L_target / baseline)
        return primary.turns * ratio

    # Bracket-search for the residual root.
    n_low, n_high = 0.5, 200.0
    f_low = residual(n_low)
    f_high = residual(n_high)
    if f_low * f_high > 0:
        # Could not bracket — return current value as a fallback.
        return primary.turns
    n_solved = brentq(residual, n_low, n_high, xtol=1e-6, maxiter=200)
    return float(n_solved)


def tuning_ratio(f_secondary_hz: float, f_primary_hz: float) -> float:
    """Return the dimensionless tuning ratio ``f_sec / f_pri``."""
    if f_primary_hz <= 0:
        return 0.0
    return f_secondary_hz / f_primary_hz


def auto_tune_primary(
    secondary_frequency_hz: float, primary: PrimaryInput
) -> Tuple[PrimaryInput, PrimaryOutput]:
    """Run auto-tune and return both the geometry-consistent primary and outputs.

    For a flat spiral the outer radius is rebuilt as ``r1 + N_new · pitch``
    so that the geometry actually corresponds to the new turn count. For a
    helical primary the upper height ``h2`` is similarly rebuilt.
    """
    n_new = auto_tune(secondary_frequency_hz, primary)

    flat = math.isclose(primary.height_1, primary.height_2, abs_tol=1e-9)
    same_radius = math.isclose(primary.radius_1, primary.radius_2, abs_tol=1e-9)

    update: dict = {"turns": n_new}
    if flat and not same_radius:
        pitch = _flat_spiral_pitch(primary)
        update["radius_2"] = primary.radius_1 + n_new * pitch
    elif same_radius and not flat:
        pitch = _helical_pitch(primary)
        sign = 1.0 if primary.height_2 >= primary.height_1 else -1.0
        update["height_2"] = primary.height_1 + sign * n_new * pitch

    new_primary = primary.model_copy(update=update)
    out = calculate_primary(new_primary)
    out_with_tuning = out.model_copy(
        update={"tuning_ratio": tuning_ratio(secondary_frequency_hz, out.resonant_frequency_hz)}
    )
    return new_primary, out_with_tuning
