"""Coupling coefficient between primary and secondary coils.

The coupling coefficient ``k`` measures how much of the primary's stored
energy can be transferred to the secondary per RF cycle:

    k = M / √(L_pri · L_sec)

The mutual inductance ``M`` is computed by the **filamentary** method:
each turn of each coil is treated as a thin circular loop and the mutual
inductance between every pair of loops is computed using complete elliptic
integrals K and E (the closed-form solution due to Maxwell). A fractional
last turn is a loop weighted by its fraction, so ``M`` is continuous in the
turn count. ``L_pri`` is the winding inductance without the leads, which do
not couple to the secondary.

This is O(N_pri · N_sec), vectorised with NumPy, which is fast for typical
Tesla coils (N_sec ≤ 2000, N_pri ≤ 30).

References
----------
- J.C. Maxwell, "A Treatise on Electricity and Magnetism" (1873) — exact
  mutual inductance of two coaxial loops via elliptic integrals.
- F.W. Grover, "Inductance Calculations" (1946), Chapter 7.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq

from pyteslacoil.engine.inductance import Filaments, filament_mutual_inductance, winding_filaments
from pyteslacoil.engine.primary import calculate_primary, primary_filaments
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.models.coupling_model import CouplingInput, CouplingOutput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput

_SCAN_SAMPLES = 81


def secondary_filaments(secondary: SecondaryInput) -> Filaments:
    """The secondary winding as circular filaments (one per turn)."""
    return winding_filaments(
        secondary.radius_1,
        secondary.radius_2,
        secondary.height_1,
        secondary.height_2,
        secondary.turns,
    )


def mutual_inductance(primary: PrimaryInput, secondary: SecondaryInput) -> float:
    """Total mutual inductance between primary and secondary coils.

    Both coils are assumed coaxial and concentric. ``height_1`` /
    ``height_2`` are measured along a common vertical axis.
    """
    return filament_mutual_inductance(primary_filaments(primary), secondary_filaments(secondary))


def coupling_coefficient(
    primary: PrimaryInput, secondary: SecondaryInput
) -> tuple[float, float, float, float]:
    """Return ``(M, k, L_pri, L_sec)`` for the given coil pair."""
    l_pri = calculate_primary(primary).inductance_h
    l_sec = calculate_secondary(secondary).inductance_h
    m = mutual_inductance(primary, secondary)
    return m, m / math.sqrt(l_pri * l_sec), l_pri, l_sec


def shift_primary(primary: PrimaryInput, dz: float) -> PrimaryInput:
    """A validated copy of ``primary`` moved vertically by ``dz`` (heights kept ≥ 0)."""
    data = primary.model_dump()
    data["height_1"] = max(0.0, primary.height_1 + dz)
    data["height_2"] = max(0.0, primary.height_2 + dz)
    return PrimaryInput.model_validate(data)


def _adjust_primary_for_k(
    primary: PrimaryInput, secondary: SecondaryInput, target_k: float
) -> tuple[PrimaryInput, bool]:
    """Shift the primary coil vertically until its k matches the target.

    Strategy: scan a vertical range that brackets the secondary (without
    moving the primary below the ground plane), locate the sign change of
    ``k(dz) − target`` closest to the current position, and refine it with
    brentq. A vertical shift changes neither coil's self-inductance, so only
    the mutual inductance is recomputed.
    """
    f_pri = primary_filaments(primary)
    f_sec = secondary_filaments(secondary)
    l_pri = calculate_primary(primary).inductance_h
    l_sec = calculate_secondary(secondary).inductance_h
    norm = math.sqrt(l_pri * l_sec)

    def residual(dz: float) -> float:
        return filament_mutual_inductance(f_pri, f_sec, dz) / norm - target_k

    span = 2.0 * max(secondary.height_2 - secondary.height_1, 0.1)
    dz_min = max(-span, -min(primary.height_1, primary.height_2))
    samples = np.linspace(dz_min, span, _SCAN_SAMPLES)
    residuals = np.array([residual(float(z)) for z in samples])

    exact = np.flatnonzero(residuals == 0.0)
    brackets = np.flatnonzero(residuals[:-1] * residuals[1:] < 0.0)
    candidates = [(abs(samples[i]), float(samples[i])) for i in exact]
    for i in brackets:
        root = brentq(residual, float(samples[i]), float(samples[i + 1]), xtol=1e-7, maxiter=200)
        candidates.append((abs(root), float(root)))
    if not candidates:
        return primary, False
    _, dz_solved = min(candidates)
    return shift_primary(primary, dz_solved), True


def calculate_coupling(
    inp: CouplingInput, operating_frequency_hz: float | None = None
) -> CouplingOutput:
    """Mutual inductance, coupling and energy-transfer time of a coil pair.

    ``operating_frequency_hz`` is the frequency used for the energy-transfer
    time; it defaults to the bare secondary resonance (pass the loaded
    system frequency when a topload is present).
    """
    primary = inp.primary
    converged: bool | None = None
    adjusted_h1 = adjusted_h2 = None
    if inp.auto_adjust_height and inp.desired_k is not None:
        primary, converged = _adjust_primary_for_k(inp.primary, inp.secondary, inp.desired_k)
        if converged:
            adjusted_h1, adjusted_h2 = primary.height_1, primary.height_2

    m, k, l_pri, l_sec = coupling_coefficient(primary, inp.secondary)

    f_op = operating_frequency_hz
    if f_op is None:
        f_op = calculate_secondary(inp.secondary).resonant_frequency_hz

    t_transfer = cycles = None
    if k > 0:
        cycles = 1.0 / (2.0 * k)
        t_transfer = cycles / f_op

    return CouplingOutput(
        mutual_inductance_h=m,
        coupling_coefficient=k,
        energy_transfer_time_s=t_transfer,
        energy_transfer_cycles=cycles,
        primary_inductance_h=l_pri,
        secondary_inductance_h=l_sec,
        adjusted_primary_height_1_m=adjusted_h1,
        adjusted_primary_height_2_m=adjusted_h2,
        adjustment_converged=converged,
    )
