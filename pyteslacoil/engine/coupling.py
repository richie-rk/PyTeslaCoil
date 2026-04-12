"""Coupling coefficient between primary and secondary coils.

The coupling coefficient ``k`` measures how much of the primary's stored
energy can be transferred to the secondary per RF cycle:

    k = M / √(L_pri · L_sec)

The mutual inductance ``M`` is computed by the **filamentary** method:
each turn of each coil is treated as a thin circular loop and the mutual
inductance between every pair of loops is computed using complete elliptic
integrals K and E (the closed-form solution due to Maxwell). The total is
then summed.

This is O(N_pri · N_sec) which is fine for typical Tesla coils
(N_sec ≤ 2000, N_pri ≤ 30 → 60 000 pairs ≈ <50 ms).

References
----------
- J.C. Maxwell, "A Treatise on Electricity and Magnetism" (1873) — exact
  mutual inductance of two coaxial loops via elliptic integrals.
- F.W. Grover, "Inductance Calculations" (1946), Chapter 7.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from scipy.optimize import brentq
from scipy.special import ellipe, ellipk

from pyteslacoil.constants import MU_0, PI
from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.models.coupling_model import CouplingInput, CouplingOutput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput


def _filaments_for_primary(p: PrimaryInput) -> Tuple[np.ndarray, np.ndarray]:
    n = max(1, int(round(p.turns)))
    radii = np.linspace(p.radius_1, p.radius_2, n)
    heights = np.linspace(p.height_1, p.height_2, n)
    return radii, heights


def _filaments_for_secondary(s: SecondaryInput) -> Tuple[np.ndarray, np.ndarray]:
    n = max(1, int(s.turns))
    radii = np.linspace(s.radius_1, s.radius_2, n)
    heights = np.linspace(s.height_1, s.height_2, n)
    return radii, heights


def _mutual_pair_vec(
    r_pri: np.ndarray, h_pri: np.ndarray, r_sec: np.ndarray, h_sec: np.ndarray
) -> float:
    """Vectorized total mutual inductance over all (i, j) filament pairs.

    Returns sum_{i,j} M(r_pri[i], r_sec[j], |h_pri[i] - h_sec[j]|).
    """
    # Build broadcast 2D arrays.
    R1 = r_pri[:, None]      # shape (Np, 1)
    R2 = r_sec[None, :]      # shape (1, Ns)
    D = np.abs(h_pri[:, None] - h_sec[None, :])  # shape (Np, Ns)

    denom = (R1 + R2) ** 2 + D * D
    k_sq = 4.0 * R1 * R2 / denom
    # Numerical safety:
    np.clip(k_sq, 0.0, 1.0 - 1e-15, out=k_sq)
    k = np.sqrt(k_sq)

    K = ellipk(k_sq)
    E = ellipe(k_sq)

    factor = MU_0 * np.sqrt(R1 * R2)
    M_pair = factor * ((2.0 / k - k) * K - (2.0 / k) * E)

    return float(M_pair.sum())


def mutual_inductance(primary: PrimaryInput, secondary: SecondaryInput) -> float:
    """Total mutual inductance between primary and secondary coils.

    Both coils are assumed coaxial and concentric. ``height_1`` /
    ``height_2`` are measured along a common vertical axis.
    """
    r_pri, h_pri = _filaments_for_primary(primary)
    r_sec, h_sec = _filaments_for_secondary(secondary)
    return _mutual_pair_vec(r_pri, h_pri, r_sec, h_sec)


def coupling_coefficient(
    primary: PrimaryInput, secondary: SecondaryInput
) -> Tuple[float, float, float, float]:
    """Return ``(M, k, L_pri, L_sec)`` for the given coil pair."""
    L_pri = calculate_primary(primary).inductance_h
    L_sec = calculate_secondary(secondary).inductance_h
    M = mutual_inductance(primary, secondary)
    if L_pri <= 0 or L_sec <= 0:
        return M, 0.0, L_pri, L_sec
    k = M / math.sqrt(L_pri * L_sec)
    return M, k, L_pri, L_sec


def _shifted_primary(primary: PrimaryInput, dz: float) -> PrimaryInput:
    return primary.model_copy(
        update={"height_1": primary.height_1 + dz, "height_2": primary.height_2 + dz}
    )


def _adjust_primary_for_k(
    primary: PrimaryInput, secondary: SecondaryInput, target_k: float
) -> Tuple[PrimaryInput, bool]:
    """Shift the primary coil vertically until its k matches the target.

    Strategy: do a coarse scan over a vertical range that brackets the
    secondary, then locate the first sign change of ``k(dz) − target`` and
    refine with brentq. The k-vs-dz curve is generally unimodal (it peaks
    when the primary sits near the secondary base and falls off in either
    direction), so a coarse scan reliably catches the closest root.
    """
    sec_height = secondary.height_2 - secondary.height_1
    span = 2.0 * max(sec_height, 0.1)

    def residual(dz: float) -> float:
        shifted = _shifted_primary(primary, dz)
        _, k, _, _ = coupling_coefficient(shifted, secondary)
        return k - target_k

    # Coarse scan with 41 samples across the span.
    n = 41
    samples = np.linspace(-span, +span, n)
    residuals = np.array([residual(float(z)) for z in samples])

    # Find any adjacent pair of opposite signs.
    sign_changes = np.where(residuals[:-1] * residuals[1:] < 0.0)[0]
    if len(sign_changes) == 0:
        return primary, False

    # Pick the sign change closest to dz=0 (i.e. the smallest move).
    abs_z = [abs(0.5 * (samples[i] + samples[i + 1])) for i in sign_changes]
    best = sign_changes[int(np.argmin(abs_z))]

    dz_solved = brentq(
        residual, float(samples[best]), float(samples[best + 1]),
        xtol=1e-6, maxiter=200,
    )
    return _shifted_primary(primary, float(dz_solved)), True


def calculate_coupling(inp: CouplingInput) -> CouplingOutput:
    M, k, L_pri, L_sec = coupling_coefficient(inp.primary, inp.secondary)

    sec_out = calculate_secondary(inp.secondary)
    f_res = sec_out.resonant_frequency_hz

    if k > 0 and f_res > 0:
        t_transfer = 1.0 / (2.0 * k * f_res)
        cycles = 1.0 / (2.0 * k)
    else:
        t_transfer = float("inf")
        cycles = float("inf")

    adjusted_h1 = None
    adjusted_h2 = None
    converged = True
    if inp.auto_adjust_height and inp.desired_k is not None:
        adjusted, converged = _adjust_primary_for_k(
            inp.primary, inp.secondary, inp.desired_k
        )
        adjusted_h1 = adjusted.height_1
        adjusted_h2 = adjusted.height_2
        # Recompute k for the adjusted geometry so the user sees the result.
        if converged:
            M, k, L_pri, L_sec = coupling_coefficient(adjusted, inp.secondary)

    return CouplingOutput(
        mutual_inductance_h=M,
        mutual_inductance_uh=M * 1e6,
        coupling_coefficient=k,
        energy_transfer_time_s=t_transfer,
        energy_transfer_cycles=cycles,
        primary_inductance_h=L_pri,
        secondary_inductance_h=L_sec,
        adjusted_primary_height_1_m=adjusted_h1,
        adjusted_primary_height_2_m=adjusted_h2,
        adjustment_converged=converged,
    )
