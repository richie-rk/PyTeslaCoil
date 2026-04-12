"""Spark length estimator tests."""

import pytest

from pyteslacoil.engine.spark_length import (
    estimate_spark_length,
    spark_length_from_energy,
    spark_length_from_power,
)
from pyteslacoil.units import meters_to_inches


def test_freau_500w_about_38in():
    """Freau predicts L = 1.7 · √500 ≈ 38 in for a 500 W coil."""
    L = spark_length_from_power(500.0)
    assert meters_to_inches(L) == pytest.approx(38.0, rel=0.05)


def test_zero_power_zero_length():
    assert spark_length_from_power(0.0) == 0.0
    assert spark_length_from_energy(0.0, 0.0) == 0.0


def test_estimate_prefers_energy_form():
    """When both inputs are given the energy form takes precedence."""
    L = estimate_spark_length(input_power_watts=500, bps=120, energy_per_bang_j=4.0)
    expected = spark_length_from_energy(120, 4.0)
    assert L == pytest.approx(expected)
