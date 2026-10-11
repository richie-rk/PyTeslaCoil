"""Spark gap (static and rotary) tests."""

import numpy as np
import pytest

from pyteslacoil.engine.spark_gap_rotary import calculate_rotary_gap, charge_fraction
from pyteslacoil.engine.spark_gap_static import air_breakdown_voltage, calculate_static_gap
from pyteslacoil.models.spark_gap_model import RotaryGapInput, StaticGapInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def _static(**overrides) -> StaticGapInput:
    data = dict(
        num_electrodes=4,
        electrode_diameter=inches_to_meters(0.5),
        total_gap_spacing=inches_to_meters(0.15),
        transformer_voltage_peak=12_000.0 * 1.414,
        tank_capacitance=nf_to_farads(10.0),
        line_frequency_hz=60.0,
    )
    data.update(overrides)
    return StaticGapInput(**data)


def _rotary(**overrides) -> RotaryGapInput:
    data = dict(
        num_stationary_electrodes=2,
        num_rotating_electrodes=8,
        disc_rpm=3000.0,
        rotating_electrode_diameter=0.005,
        stationary_electrode_diameter=0.005,
        rotating_path_diameter=0.20,
        transformer_voltage_peak=15_000.0,
        tank_capacitance=nf_to_farads(20.0),
    )
    data.update(overrides)
    return RotaryGapInput(**data)


def test_breakdown_voltage_monotonic():
    """Wider gap → higher breakdown voltage."""
    a = air_breakdown_voltage(0.001)
    b = air_breakdown_voltage(0.005)
    c = air_breakdown_voltage(0.020)
    assert a < b < c


def test_breakdown_voltage_1cm_about_30kv():
    assert air_breakdown_voltage(0.01) == pytest.approx(30_300.0, rel=0.01)


def test_static_gap_basic():
    out = calculate_static_gap(_static())
    assert out.fires
    assert out.bps == pytest.approx(120.0)
    assert out.gap_per_electrode_m == pytest.approx(inches_to_meters(0.05))
    assert 0 < out.percent_cap_charged <= 100
    assert out.effective_cap_energy_j == pytest.approx(
        0.5 * nf_to_farads(10.0) * out.breakdown_voltage_v**2
    )
    assert out.time_to_arc_s is not None and out.time_to_arc_s < 1 / 240
    assert out.spark_length_m > 0


def test_static_gap_that_cannot_fire_produces_no_sparks():
    out = calculate_static_gap(_static(num_electrodes=2, total_gap_spacing=0.02))
    assert out.breakdown_voltage_v > 12_000.0 * 1.414
    assert not out.fires
    assert out.bps == 0.0
    assert out.effective_cap_energy_j == 0.0
    assert out.spark_length_m == 0.0
    assert out.time_to_arc_s is None


def test_standalone_gap_needs_tank_parameters():
    with pytest.raises(ValueError):
        calculate_static_gap(_static(transformer_voltage_peak=None))
    with pytest.raises(ValueError):
        calculate_rotary_gap(_rotary(tank_capacitance=None))


def test_rotary_series_pair_bps():
    """Two stationary electrodes fire as one series pair: BPS = rotating × RPM / 60."""
    out = calculate_rotary_gap(_rotary())
    assert out.presentations_per_revolution == 16
    assert out.breaks_per_revolution == 8
    assert out.bps == pytest.approx(8 * 50.0)
    assert out.firing_period_s == pytest.approx(1 / 400)
    assert out.rotational_speed_m_per_s > 0
    assert out.spark_length_m > 0


def test_classic_synchronous_rotary_is_120_bps():
    """Four rotating electrodes on an 1800 RPM motor: the classic 120 BPS SRSG."""
    out = calculate_rotary_gap(_rotary(num_rotating_electrodes=4, disc_rpm=1800.0))
    assert out.bps == pytest.approx(120.0)


def test_rotary_charge_is_monotonic_and_continuous_in_bps():
    """Slower firing never charges the capacitor less (no cliff above 120 BPS)."""
    rpms = np.linspace(300.0, 6000.0, 400)
    charge = [calculate_rotary_gap(_rotary(num_rotating_electrodes=4, disc_rpm=r)).percent_cap_charged for r in rpms]
    assert all(a >= b - 1e-9 for a, b in zip(charge, charge[1:], strict=False))
    assert max(abs(a - b) for a, b in zip(charge, charge[1:], strict=False)) < 2.0


def test_charge_fraction_reaches_full_charge_after_a_quarter_cycle():
    assert charge_fraction(1 / 240, 60.0) == pytest.approx(1.0)
    assert charge_fraction(1 / 120, 60.0) == pytest.approx(1.0)
    assert charge_fraction(1 / 480, 60.0) == pytest.approx(np.sin(np.pi / 4))
