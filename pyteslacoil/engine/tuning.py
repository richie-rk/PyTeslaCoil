"""Auto-tune: find the primary turns count that matches the secondary.

The primary tank circuit is tuned by moving the tap point, i.e. by changing
how many turns of a winding with a fixed pitch are in circuit. Given the
target (secondary) frequency we solve for the turn count ``N`` such that

    f_pri(N) = 1 / (2π · √((L_coil(N) + L_lead) · C_tank))  ==  f_target

with the winding extended (or shortened) along its own direction so that the
radial and axial pitch stay constant. ``L_coil`` grows monotonically with
``N``, so the root is unique and is found with :func:`scipy.optimize.brentq`.
"""

from __future__ import annotations

from scipy.optimize import brentq

from pyteslacoil.engine.primary import calculate_primary, lead_inductance, primary_coil_inductance
from pyteslacoil.engine.resonance import inductance_for_frequency
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput

TURNS_SEARCH_RANGE: tuple[float, float] = (0.25, 250.0)
"""Smallest and largest primary turn counts auto-tune will consider."""


class AutoTuneError(ValueError):
    """Raised when no tap point in :data:`TURNS_SEARCH_RANGE` matches the target."""


def required_primary_inductance(target_frequency_hz: float, c_tank: float) -> float:
    """The total primary inductance required to resonate at ``target_frequency_hz``.

        L = 1 / ((2π · f)² · C)
    """
    return inductance_for_frequency(target_frequency_hz, c_tank)


def tuned_primary_geometry(primary: PrimaryInput, turns: float) -> PrimaryInput:
    """``primary`` tapped at ``turns`` turns, keeping its radial and axial pitch.

    The start point ``(radius_1, height_1)`` stays where it is and the end
    point moves along the winding. Raises :class:`ValueError` if the
    extended winding would leave the valid range (radius ≤ 0 or height < 0).
    """
    dr = (primary.radius_2 - primary.radius_1) / primary.turns
    dh = (primary.height_2 - primary.height_1) / primary.turns
    data = primary.model_dump()
    data.update(
        turns=turns,
        radius_2=primary.radius_1 + turns * dr,
        height_2=primary.height_1 + turns * dh,
    )
    return PrimaryInput.model_validate(data)


def _max_turns(primary: PrimaryInput) -> float:
    """Largest turn count whose extended geometry stays valid."""
    limit = TURNS_SEARCH_RANGE[1]
    dr = (primary.radius_2 - primary.radius_1) / primary.turns
    dh = (primary.height_2 - primary.height_1) / primary.turns
    if dr < 0:
        limit = min(limit, 0.999 * primary.radius_1 / -dr)
    if dh < 0:
        limit = min(limit, 0.999 * primary.height_1 / -dh)
    return limit


def auto_tune(secondary_frequency_hz: float, primary: PrimaryInput) -> float:
    """Compute the (fractional) primary turn count that matches the secondary.

    Parameters
    ----------
    secondary_frequency_hz
        Target frequency, normally the loaded (with topload) secondary
        resonance.
    primary
        The primary input; its geometry and turn count define the winding
        pitch, and its capacitance and lead inductance are included. The
        object is not modified.

    Returns
    -------
    float
        The primary turns count (can be fractional, e.g. ``10.832``).

    Raises
    ------
    AutoTuneError
        If no turn count in :data:`TURNS_SEARCH_RANGE` resonates at the
        target frequency.
    """
    l_target = required_primary_inductance(secondary_frequency_hz, primary.capacitance)
    l_lead = lead_inductance(primary.lead_length, primary.lead_diameter)
    if l_lead >= l_target:
        raise AutoTuneError(
            "the lead inductance alone exceeds the inductance needed to reach "
            f"{secondary_frequency_hz / 1e3:.1f} kHz; shorten the leads or reduce the capacitance"
        )

    def residual(n: float) -> float:
        return primary_coil_inductance(tuned_primary_geometry(primary, n)) + l_lead - l_target

    n_low, n_high = TURNS_SEARCH_RANGE[0], _max_turns(primary)
    if n_high <= n_low:
        raise AutoTuneError("the winding direction leaves no room to add turns")
    if residual(n_low) > 0:
        raise AutoTuneError(
            f"even {n_low:g} turns resonate below {secondary_frequency_hz / 1e3:.1f} kHz; "
            "reduce the tank capacitance or the winding radius"
        )
    if residual(n_high) < 0:
        raise AutoTuneError(
            f"more than {n_high:.4g} turns would be needed to reach "
            f"{secondary_frequency_hz / 1e3:.1f} kHz; increase the tank capacitance"
        )
    return float(brentq(residual, n_low, n_high, xtol=1e-9, rtol=1e-10, maxiter=200))


def tuning_ratio(f_secondary_hz: float, f_primary_hz: float) -> float:
    """Return the dimensionless tuning ratio ``f_sec / f_pri``."""
    if f_primary_hz <= 0:
        raise ValueError(f"f_primary_hz must be positive, got {f_primary_hz!r}")
    return f_secondary_hz / f_primary_hz


def auto_tune_primary(
    secondary_frequency_hz: float, primary: PrimaryInput
) -> tuple[PrimaryInput, PrimaryOutput]:
    """Run auto-tune and return the tuned primary geometry and its outputs.

    The returned geometry is consistent with the new turn count (see
    :func:`tuned_primary_geometry`); its output carries the tuning ratio.
    Raises :class:`AutoTuneError` like :func:`auto_tune`.
    """
    n_new = auto_tune(secondary_frequency_hz, primary)
    new_primary = tuned_primary_geometry(primary, n_new)
    out = calculate_primary(new_primary)
    ratio = tuning_ratio(secondary_frequency_hz, out.resonant_frequency_hz)
    return new_primary, out.model_copy(update={"tuning_ratio": ratio})
