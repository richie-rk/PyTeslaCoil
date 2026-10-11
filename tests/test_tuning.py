"""Auto-tune tests."""

import pytest

from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.tuning import (
    AutoTuneError,
    auto_tune,
    auto_tune_primary,
    required_primary_inductance,
    tuned_primary_geometry,
    tuning_ratio,
)
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def _primary(**overrides) -> PrimaryInput:
    data = dict(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(8.0),
        turns=12.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    data.update(overrides)
    return PrimaryInput(**data)


def test_required_inductance_known_case():
    """At 100 kHz with 10 nF, L should be ≈ 253 µH."""
    assert required_primary_inductance(100_000.0, 10e-9) == pytest.approx(2.533e-4, rel=0.001)


def test_tuning_ratio():
    assert tuning_ratio(100e3, 100e3) == pytest.approx(1.0)
    assert tuning_ratio(100e3, 200e3) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        tuning_ratio(100e3, 0)


@pytest.mark.parametrize(
    ("geometry", "target"),
    [
        ({}, 200_000.0),  # helical
        ({"radius_2": inches_to_meters(8.0), "height_2": 0.0}, 150_000.0),  # flat spiral
        ({"radius_2": inches_to_meters(6.0), "height_2": inches_to_meters(3.0)}, 180_000.0),  # conical
    ],
)
def test_auto_tune_hits_target_including_lead_inductance(geometry, target):
    pri = _primary(lead_length=1.5, **geometry)
    tuned, out = auto_tune_primary(target, pri)
    assert out.resonant_frequency_hz == pytest.approx(target, rel=1e-6)
    assert out.tuning_ratio == pytest.approx(1.0, rel=1e-6)
    assert calculate_primary(tuned).resonant_frequency_hz == pytest.approx(target, rel=1e-6)


def test_tuned_geometry_keeps_the_winding_pitch():
    pri = _primary(radius_2=inches_to_meters(6.0), height_2=inches_to_meters(3.0), turns=10.0)
    tuned = tuned_primary_geometry(pri, 15.0)
    assert (tuned.radius_2 - tuned.radius_1) / tuned.turns == pytest.approx(
        (pri.radius_2 - pri.radius_1) / pri.turns
    )
    assert (tuned.height_2 - tuned.height_1) / tuned.turns == pytest.approx(
        (pri.height_2 - pri.height_1) / pri.turns
    )


def test_auto_tune_does_not_modify_its_input():
    pri = _primary()
    before = pri.model_dump()
    auto_tune(200_000.0, pri)
    assert pri.model_dump() == before


def test_auto_tune_reports_impossible_targets():
    with pytest.raises(AutoTuneError):
        auto_tune(5_000.0, _primary())  # would need far more than 250 turns
    with pytest.raises(AutoTuneError):
        auto_tune(5e7, _primary(lead_length=5.0))  # the leads alone are too inductive
