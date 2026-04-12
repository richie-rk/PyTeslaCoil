"""Coupling coefficient tests."""

import math

import pytest

from pyteslacoil.engine.coupling import (
    calculate_coupling,
    coupling_coefficient,
    mutual_inductance,
)
from pyteslacoil.models.coupling_model import CouplingInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def _typical_pair() -> tuple[PrimaryInput, SecondaryInput]:
    """A typical small SGTC: flat spiral primary with the secondary base
    a couple of inches above it. Coupling lands in the usual 0.1-0.25 range."""
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


def test_mutual_positive_for_concentric_coils():
    pri, sec = _typical_pair()
    M = mutual_inductance(pri, sec)
    assert M > 0


def test_coupling_coefficient_in_typical_range():
    """k for a Tesla coil is normally in 0.05–0.30."""
    pri, sec = _typical_pair()
    _, k, _, _ = coupling_coefficient(pri, sec)
    assert 0.02 < k < 0.40


def test_coupling_drops_when_primary_lifted_far_above():
    """Lifting the primary far above the secondary should drop k."""
    pri, sec = _typical_pair()
    far = pri.model_copy(update={"height_1": 5.0, "height_2": 5.0})
    _, k_close, _, _ = coupling_coefficient(pri, sec)
    _, k_far, _, _ = coupling_coefficient(far, sec)
    assert k_far < k_close


def test_calculate_coupling_returns_full_output():
    pri, sec = _typical_pair()
    out = calculate_coupling(CouplingInput(primary=pri, secondary=sec))
    assert out.coupling_coefficient > 0
    assert out.mutual_inductance_h > 0
    assert math.isfinite(out.energy_transfer_time_s)
    assert out.energy_transfer_cycles > 1.0


def test_auto_adjust_height_converges():
    pri, sec = _typical_pair()
    out = calculate_coupling(
        CouplingInput(
            primary=pri,
            secondary=sec,
            desired_k=0.15,
            auto_adjust_height=True,
        )
    )
    assert out.adjustment_converged
    assert out.adjusted_primary_height_1_m is not None
    assert out.coupling_coefficient == pytest.approx(0.15, abs=0.01)
