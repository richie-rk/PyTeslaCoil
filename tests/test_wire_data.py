"""Sanity checks on the AWG wire table."""

import pytest

from pyteslacoil import wire_data


def test_known_gauges_present():
    for awg in (10, 20, 24, 30, 40):
        assert awg in wire_data.AWG_TABLE


def test_diameter_follows_the_awg_definition():
    assert wire_data.AWG_TABLE[36]["bare_diameter_in"] == pytest.approx(0.005)
    assert wire_data.AWG_TABLE[24]["bare_diameter_in"] == pytest.approx(0.0201, abs=5e-5)
    assert wire_data.AWG_TABLE[4]["bare_diameter_in"] == pytest.approx(0.2043, abs=5e-5)


def test_resistance_is_annealed_copper_at_20c():
    """AWG 24 is 84.2 mΩ/m (25.67 Ω per 1000 ft) at 20 °C."""
    assert wire_data.resistance_per_meter(24) == pytest.approx(0.08422, rel=0.002)
    assert wire_data.AWG_TABLE[24]["resistance_per_ft"] == pytest.approx(0.02567, rel=0.002)


def test_diameter_decreases_with_gauge():
    """Larger AWG = thinner wire."""
    diams = [wire_data.AWG_TABLE[g]["bare_diameter_in"] for g in sorted(wire_data.AWG_TABLE)]
    assert diams == sorted(diams, reverse=True)


def test_resistance_increases_with_gauge():
    res = [wire_data.AWG_TABLE[g]["resistance_per_m"] for g in sorted(wire_data.AWG_TABLE)]
    assert res == sorted(res)


def test_insulated_wire_is_thicker_than_bare():
    for gauge, row in wire_data.AWG_TABLE.items():
        assert row["insulated_diameter_in"] > row["bare_diameter_in"], gauge


def test_meters_cache_consistent():
    for gauge, row in wire_data.AWG_TABLE.items():
        assert row["bare_diameter_m"] == pytest.approx(row["bare_diameter_in"] * 0.0254), gauge


def test_table_is_read_only():
    with pytest.raises(TypeError):
        wire_data.AWG_TABLE[24]["bare_diameter_m"] = 1.0


def test_get_wire_unknown_raises():
    with pytest.raises(KeyError):
        wire_data.get_wire(99)
