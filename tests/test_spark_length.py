"""Spark length estimator tests."""

import math

import pytest

from pyteslacoil.engine.spark_length import (
    estimate_spark_length,
    spark_length_from_energy,
    spark_length_from_power,
    terminal_voltage_estimate,
)
from pyteslacoil.units import meters_to_inches


def test_freau_500w_about_38in():
    """Freau predicts L = 1.7 · √500 ≈ 38 in for a 500 W coil."""
    assert meters_to_inches(spark_length_from_power(500.0)) == pytest.approx(1.7 * math.sqrt(500))


def test_zero_power_zero_length():
    assert spark_length_from_power(0.0) == 0.0
    assert spark_length_from_energy(0.0, 0.0) == 0.0


def test_energy_form_equals_power_form():
    assert spark_length_from_energy(120, 4.0) == pytest.approx(spark_length_from_power(480.0))


def test_estimate_prefers_energy_form():
    """When both inputs are given the energy form takes precedence."""
    length = estimate_spark_length(input_power_watts=500, bps=120, energy_per_bang_j=4.0)
    assert length == pytest.approx(spark_length_from_energy(120, 4.0))


def test_terminal_voltage_uses_the_given_capacitance():
    assert terminal_voltage_estimate(1.0, 20e-12) == pytest.approx(math.sqrt(2.0 / 20e-12))
    assert terminal_voltage_estimate(1.0) == pytest.approx(math.sqrt(2.0 / 30e-12))
    assert terminal_voltage_estimate(0.0, 20e-12) == 0.0
