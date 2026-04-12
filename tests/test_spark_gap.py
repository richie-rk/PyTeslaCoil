"""Spark gap (static and rotary) tests."""

import pytest

from pyteslacoil.engine.spark_gap_rotary import calculate_rotary_gap
from pyteslacoil.engine.spark_gap_static import (
    air_breakdown_voltage,
    calculate_static_gap,
)
from pyteslacoil.models.spark_gap_model import RotaryGapInput, StaticGapInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def test_breakdown_voltage_monotonic():
    """Wider gap → higher breakdown voltage."""
    a = air_breakdown_voltage(0.001)
    b = air_breakdown_voltage(0.005)
    c = air_breakdown_voltage(0.020)
    assert a < b < c


def test_breakdown_voltage_1mm_about_3kv():
    v = air_breakdown_voltage(0.001)
    assert 2_000 < v < 6_000


def test_static_gap_basic():
    inp = StaticGapInput(
        num_electrodes=4,
        electrode_diameter=inches_to_meters(0.5),
        total_gap_spacing=inches_to_meters(0.15),
        transformer_voltage_peak=12_000.0 * 1.414,
        tank_capacitance=nf_to_farads(10.0),
        line_frequency_hz=60.0,
    )
    out = calculate_static_gap(inp)
    assert out.bps == pytest.approx(120.0)
    assert out.gap_per_electrode_m > 0
    assert out.breakdown_voltage_v > 0
    assert 0 <= out.percent_cap_charged <= 100
    assert out.effective_cap_energy_j > 0
    assert out.spark_length_m > 0


def test_rotary_gap_bps_formula():
    """BPS = stationary × rotating × (RPM / 60)."""
    inp = RotaryGapInput(
        num_stationary_electrodes=2,
        num_rotating_electrodes=8,
        disc_rpm=3000.0,
        rotating_electrode_diameter=0.005,
        stationary_electrode_diameter=0.005,
        rotating_path_diameter=0.20,
        transformer_voltage_peak=15_000.0,
        tank_capacitance=nf_to_farads(20.0),
    )
    out = calculate_rotary_gap(inp)
    assert out.presentations_per_revolution == 16
    assert out.bps == pytest.approx(16 * 50.0)  # 3000 RPM = 50 rps
    assert out.rotational_speed_m_per_s > 0
    assert out.spark_length_m > 0
