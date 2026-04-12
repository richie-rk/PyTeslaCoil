"""Tests for the Medhurst self-capacitance interpolator."""

import pytest

from pyteslacoil.engine import medhurst


def test_table_endpoints():
    assert medhurst.medhurst_coefficient(0.10) == pytest.approx(0.96)
    assert medhurst.medhurst_coefficient(5.00) == pytest.approx(0.38)


def test_clamp_below_range():
    assert medhurst.medhurst_coefficient(0.01) == pytest.approx(0.96)


def test_clamp_above_range():
    assert medhurst.medhurst_coefficient(50.0) == pytest.approx(0.38)


def test_interpolation_monotonic():
    """H decreases monotonically with L/D ratio over the table."""
    ratios = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    coeffs = [medhurst.medhurst_coefficient(r) for r in ratios]
    assert coeffs == sorted(coeffs, reverse=True)


def test_self_capacitance_typical():
    """A 10 cm diameter, 30 cm long secondary should give a few-pF self-cap."""
    c_pf = medhurst.self_capacitance_pf(length_m=0.30, diameter_m=0.10)
    # Ratio = 3.0 → H ≈ 0.39 → C = 0.39 * 10 cm = 3.9 pF
    assert c_pf == pytest.approx(3.9, rel=0.01)


def test_self_capacitance_zero_diameter_raises():
    with pytest.raises(ValueError):
        medhurst.self_capacitance_pf(0.3, 0.0)
