"""Tests for the Medhurst self-capacitance interpolator."""

import numpy as np
import pytest

from pyteslacoil.engine import medhurst


@pytest.mark.parametrize(
    ("ratio", "h"),
    [(0.10, 0.96), (0.50, 0.50), (1.00, 0.46), (2.00, 0.50), (3.00, 0.61), (4.00, 0.72), (5.00, 0.81)],
)
def test_table_values(ratio, h):
    assert medhurst.medhurst_coefficient(ratio) == pytest.approx(h)


def test_clamp_below_range():
    assert medhurst.medhurst_coefficient(0.01) == pytest.approx(0.96)


def test_long_coils_follow_medhursts_asymptote():
    """H keeps growing for long coils: Medhurst gives about 5.8 at l/D = 50."""
    assert medhurst.medhurst_coefficient(50.0) == pytest.approx(5.8, abs=0.05)
    # Continuous at the end of the table.
    assert medhurst.medhurst_coefficient(10.0 + 1e-9) == pytest.approx(
        medhurst.medhurst_coefficient(10.0)
    )


def test_minimum_near_unity_aspect_ratio():
    """H falls to a broad minimum of 0.46 around l/D ≈ 1 and rises on both sides."""
    ratios = np.linspace(0.1, 20.0, 400)
    coeffs = [medhurst.medhurst_coefficient(r) for r in ratios]
    assert min(coeffs) == pytest.approx(0.46)
    assert 0.7 <= ratios[int(np.argmin(coeffs))] <= 1.1
    assert coeffs[-1] > coeffs[int(np.argmin(coeffs))]


def test_self_capacitance_typical():
    """A 10 cm diameter, 30 cm long secondary: l/D = 3 → H = 0.61 → 6.1 pF."""
    assert medhurst.self_capacitance_pf(length_m=0.30, diameter_m=0.10) == pytest.approx(6.1)


def test_self_capacitance_zero_diameter_raises():
    with pytest.raises(ValueError):
        medhurst.self_capacitance_pf(0.3, 0.0)
