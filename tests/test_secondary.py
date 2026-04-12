"""Secondary coil engine tests."""

import math

import pytest

from pyteslacoil.engine.secondary import (
    calculate_secondary,
    skin_depth,
    wheeler_solenoid_inductance,
    wire_length_for_secondary,
)
from pyteslacoil.models.coil_design import CoilGeometry
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.units import inches_to_meters


def test_wheeler_dimensional():
    """Wheeler's formula returns inductance proportional to N²."""
    L1 = wheeler_solenoid_inductance(100, 0.05, 0.30)
    L2 = wheeler_solenoid_inductance(200, 0.05, 0.30)
    # 4× the turns → ~4× the L (length term doesn't change with turns).
    assert L2 / L1 == pytest.approx(4.0, rel=0.01)


def test_wire_length_solenoid_exact():
    """For a solenoid wire length = N · 2π · r."""
    n, r = 500, 0.05
    L = wire_length_for_secondary(n, r, r)
    assert L == pytest.approx(n * 2 * math.pi * r, rel=1e-9)


def test_skin_depth_1mhz_about_65um():
    """Copper skin depth at 1 MHz is ~65 µm."""
    delta = skin_depth(1e6)
    assert delta == pytest.approx(6.5e-5, rel=0.05)


def test_secondary_solenoid_typical():
    """A 4.25-in OD, 16-in long, 711-turn AWG24 secondary should resonate
    in the typical Tesla coil range and have a sensible inductance."""
    inp = SecondaryInput(
        radius_1=inches_to_meters(2.125),
        radius_2=inches_to_meters(2.125),
        height_1=inches_to_meters(3.0),
        height_2=inches_to_meters(19.0),
        turns=711,
        wire_awg=24,
    )
    out = calculate_secondary(inp)

    assert out.coil_geometry == CoilGeometry.SOLENOID
    # Inductance in the milliHenry range for this geometry.
    assert 5e-3 < out.inductance_h < 100e-3
    # Bare-secondary resonant frequency (no topload) is high; with a
    # typical topload it lands in the usual 100-400 kHz operating range.
    assert 200e3 < out.resonant_frequency_hz < 1.5e6
    # Q should be hundreds of ohms-equivalent.
    assert out.q_factor > 50.0
    # Wire length should be plausible.
    assert out.wire_length_m == pytest.approx(
        711 * 2 * math.pi * inches_to_meters(2.125), rel=1e-6
    )


def test_secondary_conical_detected():
    inp = SecondaryInput(
        radius_1=inches_to_meters(2.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(15.0),
        turns=400,
        wire_awg=22,
    )
    out = calculate_secondary(inp)
    assert out.coil_geometry == CoilGeometry.CONICAL


def test_secondary_inverse_conical():
    inp = SecondaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(2.0),
        height_1=0.0,
        height_2=inches_to_meters(15.0),
        turns=400,
        wire_awg=22,
    )
    out = calculate_secondary(inp)
    assert out.coil_geometry == CoilGeometry.INVERSE_CONICAL


def test_secondary_height_validation():
    with pytest.raises(ValueError):
        SecondaryInput(
            radius_1=0.05,
            radius_2=0.05,
            height_1=0.5,
            height_2=0.4,
            turns=300,
            wire_awg=22,
        )
