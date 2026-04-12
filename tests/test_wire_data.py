"""Sanity checks on the AWG wire table."""

import pytest

from pyteslacoil import wire_data


def test_known_gauges_present():
    for awg in (10, 20, 24, 30, 40):
        assert awg in wire_data.AWG_TABLE


def test_diameter_decreases_with_gauge():
    """Larger AWG = thinner wire."""
    diams = [wire_data.AWG_TABLE[g]["bare_diameter_in"] for g in sorted(wire_data.AWG_TABLE)]
    assert diams == sorted(diams, reverse=True)


def test_resistance_increases_with_gauge():
    res = [wire_data.AWG_TABLE[g]["resistance_per_m"] for g in sorted(wire_data.AWG_TABLE)]
    assert res == sorted(res)


def test_meters_cache_consistent():
    for g, row in wire_data.AWG_TABLE.items():
        assert row["bare_diameter_m"] == pytest.approx(row["bare_diameter_in"] * 0.0254)


def test_get_wire_unknown_raises():
    with pytest.raises(KeyError):
        wire_data.get_wire(99)
