"""Auto-tune tests."""

import pytest

from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.tuning import (
    auto_tune,
    auto_tune_primary,
    required_primary_inductance,
    tuning_ratio,
)
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def test_required_inductance_known_case():
    """At 100 kHz with 10 nF, L should be ≈ 253 µH."""
    L = required_primary_inductance(100_000.0, 10e-9)
    assert L == pytest.approx(2.533e-4, rel=0.01)


def test_tuning_ratio():
    assert tuning_ratio(100e3, 100e3) == pytest.approx(1.0)
    assert tuning_ratio(100e3, 200e3) == pytest.approx(0.5)
    assert tuning_ratio(100e3, 0) == 0.0


def test_auto_tune_helical_matches_target():
    pri = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(8.0),
        turns=12.0,  # initial guess
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    target = 200_000.0
    n = auto_tune(target, pri)
    assert n > 0
    # The geometry-consistent primary should hit the target.
    from pyteslacoil.engine.tuning import auto_tune_primary
    _, out = auto_tune_primary(target, pri)
    assert out.resonant_frequency_hz == pytest.approx(target, rel=0.05)


def test_auto_tune_flat_spiral_matches_target():
    pri = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(8.0),
        height_1=0.0,
        height_2=0.0,
        turns=12.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    target = 150_000.0
    from pyteslacoil.engine.tuning import auto_tune_primary
    _, out = auto_tune_primary(target, pri)
    assert out.resonant_frequency_hz == pytest.approx(target, rel=0.05)


def test_auto_tune_primary_helper_returns_outputs():
    pri = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(8.0),
        turns=12.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    new_pri, out = auto_tune_primary(180_000.0, pri)
    assert new_pri.turns > 0
    assert out.tuning_ratio is not None
    assert out.tuning_ratio == pytest.approx(1.0, rel=0.05)
