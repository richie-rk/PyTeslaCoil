"""Round-trip tests for unit conversions."""

import pytest

from pyteslacoil import units


@pytest.mark.parametrize("value", [0.0, 1.0, 12.5, 1000.0])
def test_inch_meter_roundtrip(value):
    assert units.meters_to_inches(units.inches_to_meters(value)) == pytest.approx(value)


@pytest.mark.parametrize("value", [0.0, 1.0, 25.4, 100.0])
def test_cm_meter_roundtrip(value):
    assert units.meters_to_cm(units.cm_to_meters(value)) == pytest.approx(value)


def test_temperature_roundtrip():
    assert units.celsius_to_fahrenheit(units.fahrenheit_to_celsius(72.0)) == pytest.approx(72.0)


def test_capacitance_units():
    assert units.farads_to_pf(1e-12) == pytest.approx(1.0)
    assert units.pf_to_farads(1.0) == pytest.approx(1e-12)
    assert units.farads_to_uf(1e-6) == pytest.approx(1.0)


def test_inductance_units():
    assert units.henries_to_uh(1e-6) == pytest.approx(1.0)
    assert units.henries_to_mh(1e-3) == pytest.approx(1.0)


def test_length_in_helper():
    assert units.length_in(0.0254, "inches") == pytest.approx(1.0)
    assert units.length_in(0.01, "cm") == pytest.approx(1.0)
    assert units.length_to_meters(1.0, "inches") == pytest.approx(0.0254)
