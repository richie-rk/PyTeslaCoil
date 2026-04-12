"""Topload module tests."""

import math

import pytest

from pyteslacoil.constants import EPSILON_0, PI
from pyteslacoil.engine.topload import (
    calculate_sphere_capacitance,
    calculate_topload,
    calculate_toroid_capacitance,
)
from pyteslacoil.models.coil_design import ToploadType
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.units import inches_to_meters


def test_sphere_capacitance_exact():
    """Sphere of 1 m diameter has C = 4πε₀ · 0.5 m."""
    C = calculate_sphere_capacitance(1.0)
    expected = 4.0 * PI * EPSILON_0 * 0.5
    assert C == pytest.approx(expected, rel=1e-9)


def test_sphere_capacitance_inches_rule_of_thumb():
    """C(pF) ≈ 1.412 · diameter[in] for an isolated sphere."""
    d_in = 12.0
    d_m = inches_to_meters(d_in)
    C = calculate_sphere_capacitance(d_m)
    pf = C * 1e12
    assert pf == pytest.approx(1.412 * d_in, rel=0.01)


def test_toroid_capacitance_typical():
    """A 4 in × 1 in toroid should be a few picofarads."""
    C = calculate_toroid_capacitance(
        major_diameter_m=inches_to_meters(4.0),
        minor_diameter_m=inches_to_meters(1.0),
    )
    pf = C * 1e12
    assert 5 < pf < 15


def test_toroid_minor_must_be_smaller():
    with pytest.raises(ValueError):
        calculate_toroid_capacitance(
            major_diameter_m=inches_to_meters(4.0),
            minor_diameter_m=inches_to_meters(4.5),
        )


def test_topload_dispatch_toroid():
    inp = ToploadInput(
        topload_type=ToploadType.TOROID,
        major_diameter=inches_to_meters(6.0),
        minor_diameter=inches_to_meters(1.5),
        height=inches_to_meters(20.0),
    )
    out = calculate_topload(inp)
    assert out.topload_type == ToploadType.TOROID
    assert out.capacitance_pf > 0


def test_topload_dispatch_sphere():
    inp = ToploadInput(
        topload_type=ToploadType.SPHERE,
        sphere_diameter=inches_to_meters(8.0),
        height=inches_to_meters(20.0),
    )
    out = calculate_topload(inp)
    assert out.topload_type == ToploadType.SPHERE
    assert out.capacitance_pf > 0


def test_topload_none_returns_zero():
    inp = ToploadInput(topload_type=ToploadType.NONE, height=0.001)
    out = calculate_topload(inp)
    assert out.capacitance_pf == 0.0
