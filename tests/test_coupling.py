"""Coupling coefficient tests."""

import math

import numpy as np
import pytest

from pyteslacoil.engine.coupling import (
    calculate_coupling,
    coupling_coefficient,
    mutual_inductance,
    shift_primary,
)
from pyteslacoil.engine.inductance import loop_mutual_inductance
from pyteslacoil.models.coupling_model import CouplingInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def _typical_pair() -> tuple[PrimaryInput, SecondaryInput]:
    """A typical small SGTC: flat spiral primary with the secondary base
    a few inches above it."""
    pri = PrimaryInput(
        radius_1=inches_to_meters(3.5),
        radius_2=inches_to_meters(8.0),
        height_1=inches_to_meters(0.5),
        height_2=inches_to_meters(0.5),
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    sec = SecondaryInput(
        radius_1=inches_to_meters(2.0),
        radius_2=inches_to_meters(2.0),
        height_1=inches_to_meters(4.5),
        height_2=inches_to_meters(20.5),
        turns=600,
        wire_awg=24,
    )
    return pri, sec


def test_loop_mutual_matches_far_field_dipole_limit():
    """Far apart, M → µ₀ π a² b² / (2 d³)."""
    a, b, d = 0.1, 0.05, 10.0
    expected = 4e-7 * math.pi * math.pi * a * a * b * b / (2 * d**3)
    assert float(loop_mutual_inductance(a, 0.0, b, d)) == pytest.approx(expected, rel=1e-3)


def test_mutual_positive_for_concentric_coils():
    pri, sec = _typical_pair()
    assert mutual_inductance(pri, sec) > 0


def test_coupling_coefficient_in_typical_range():
    """k for a spark-gap Tesla coil is normally in 0.05–0.30."""
    pri, sec = _typical_pair()
    _, k, _, _ = coupling_coefficient(pri, sec)
    assert 0.05 < k < 0.30


def test_coupling_drops_when_primary_lifted_far_above():
    pri, sec = _typical_pair()
    far = pri.model_copy(update={"height_1": 5.0, "height_2": 5.0})
    _, k_close, _, _ = coupling_coefficient(pri, sec)
    _, k_far, _, _ = coupling_coefficient(far, sec)
    assert k_far < k_close


def test_coupling_is_continuous_in_fractional_primary_turns():
    pri, sec = _typical_pair()
    ks = [
        coupling_coefficient(pri.model_copy(update={"turns": n}), sec)[1]
        for n in np.linspace(9.5, 10.5, 11)
    ]
    assert np.max(np.abs(np.diff(ks))) < 0.002


def test_calculate_coupling_returns_full_output():
    pri, sec = _typical_pair()
    out = calculate_coupling(CouplingInput(primary=pri, secondary=sec))
    assert out.coupling_coefficient > 0
    assert out.mutual_inductance_h > 0
    assert out.energy_transfer_cycles == pytest.approx(1.0 / (2.0 * out.coupling_coefficient))
    assert out.energy_transfer_time_s is not None and math.isfinite(out.energy_transfer_time_s)
    assert out.adjustment_converged is None  # no adjustment requested


def test_energy_transfer_time_uses_the_operating_frequency():
    pri, sec = _typical_pair()
    out = calculate_coupling(CouplingInput(primary=pri, secondary=sec), operating_frequency_hz=2e5)
    assert out.energy_transfer_time_s == pytest.approx(out.energy_transfer_cycles / 2e5)


def test_auto_adjust_height_converges():
    pri, sec = _typical_pair()
    out = calculate_coupling(
        CouplingInput(primary=pri, secondary=sec, desired_k=0.15, auto_adjust_height=True)
    )
    assert out.adjustment_converged is True
    assert out.adjusted_primary_height_1_m is not None
    assert out.coupling_coefficient == pytest.approx(0.15, abs=1e-4)


def test_auto_adjust_never_moves_the_primary_below_ground():
    pri, sec = _typical_pair()
    # Reaching k = 0.03 would need the primary well below the floor.
    out = calculate_coupling(
        CouplingInput(primary=pri, secondary=sec, desired_k=0.03, auto_adjust_height=True)
    )
    if out.adjustment_converged:
        assert out.adjusted_primary_height_1_m is not None
        assert out.adjusted_primary_height_1_m >= 0.0
    else:
        assert out.adjusted_primary_height_1_m is None


def test_shift_primary_validates_and_clamps_at_ground():
    pri, _ = _typical_pair()
    lowered = shift_primary(pri, -1.0)
    assert lowered.height_1 == 0.0 and lowered.height_2 == 0.0
    raised = shift_primary(pri, 0.1)
    assert raised.height_1 == pytest.approx(pri.height_1 + 0.1)
