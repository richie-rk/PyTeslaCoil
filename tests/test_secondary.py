"""Secondary coil engine tests."""

import math

import pytest
from pydantic import ValidationError

from pyteslacoil.engine.secondary import (
    ac_resistance,
    calculate_secondary,
    dc_resistance,
    skin_depth,
    wheeler_solenoid_inductance,
    wire_length_for_secondary,
)
from pyteslacoil.models.coil_design import CoilGeometry
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.units import inches_to_meters


def test_wheeler_dimensional():
    """Wheeler's formula returns inductance proportional to N²."""
    l1 = wheeler_solenoid_inductance(100, 0.05, 0.30)
    l2 = wheeler_solenoid_inductance(200, 0.05, 0.30)
    assert l2 / l1 == pytest.approx(4.0, rel=1e-12)


def test_wheeler_matches_inch_formula():
    """L[µH] = r² N² / (9 r + 10 l) with r, l in inches."""
    reference_uh = 2.125**2 * 711**2 / (9 * 2.125 + 10 * 16.0)
    computed_uh = (
        wheeler_solenoid_inductance(711, inches_to_meters(2.125), inches_to_meters(16.0)) * 1e6
    )
    assert computed_uh == pytest.approx(reference_uh, rel=0.005)


def test_wire_length_solenoid_exact():
    """For a solenoid wire length = N · 2π · r."""
    n, r = 500, 0.05
    assert wire_length_for_secondary(n, r, r) == pytest.approx(n * 2 * math.pi * r, rel=1e-9)


def test_skin_depth_1mhz_about_66um():
    """Annealed copper at 20 °C and 1 MHz: δ ≈ 66 µm."""
    assert skin_depth(1e6) == pytest.approx(6.61e-5, rel=0.01)


def test_hot_copper_has_more_resistance_and_skin_depth():
    assert dc_resistance(24, 100.0, 80.0) > dc_resistance(24, 100.0, 20.0)
    assert skin_depth(1e5, 80.0) > skin_depth(1e5, 20.0)


@pytest.mark.parametrize("x", [0.1, 0.5])
def test_ac_resistance_low_frequency_limit(x):
    """R_ac/R_dc → 1 + (a/δ)⁴/48 when the wire is thin compared to the skin depth."""
    f = 1e5
    ratio = ac_resistance(1.0, x * skin_depth(f), f)
    assert ratio == pytest.approx(1.0 + x**4 / 48.0, rel=1e-4)


@pytest.mark.parametrize("x", [5.0, 20.0, 200.0])
def test_ac_resistance_high_frequency_limit(x):
    """R_ac/R_dc → a/(2δ) + 1/4 + 3δ/(32a) for thick wires."""
    f = 1e5
    ratio = ac_resistance(1.0, x * skin_depth(f), f)
    assert ratio == pytest.approx(x / 2 + 0.25 + 3 / (32 * x), rel=1e-3)


def test_ac_resistance_is_smooth_through_the_transition():
    f = 1e5
    delta = skin_depth(f)
    ratios = [ac_resistance(1.0, x * delta, f) for x in (1.8, 1.9, 2.0, 2.1, 2.2)]
    assert ratios == sorted(ratios)
    assert ratios[2] == pytest.approx(1.2646, rel=1e-3)


def test_secondary_solenoid_typical():
    """A 4.25-in OD, 16-in long, 711-turn AWG24 secondary."""
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
    assert out.inductance_mh == pytest.approx(12.78, rel=0.005)
    # Medhurst: l/D = 3.76 → H ≈ 0.70 → C ≈ 7.5 pF for D = 10.8 cm.
    assert out.self_capacitance_pf == pytest.approx(7.52, rel=0.01)
    assert out.resonant_frequency_hz == pytest.approx(
        1.0 / (2 * math.pi * math.sqrt(out.inductance_h * out.self_capacitance_f))
    )
    assert out.ac_resistance_ohms > out.dc_resistance_ohms
    assert out.q_factor == pytest.approx(
        2 * math.pi * out.resonant_frequency_hz * out.inductance_h / out.ac_resistance_ohms
    )
    assert out.wire_length_m == pytest.approx(711 * 2 * math.pi * inches_to_meters(2.125), rel=1e-6)
    assert out.aspect_ratio == pytest.approx(16.0 / 4.25)


def test_secondary_conical_detected():
    inp = SecondaryInput(
        radius_1=inches_to_meters(2.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(15.0),
        turns=400,
        wire_awg=22,
    )
    assert calculate_secondary(inp).coil_geometry == CoilGeometry.CONICAL


def test_secondary_inverse_conical():
    inp = SecondaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(2.0),
        height_1=0.0,
        height_2=inches_to_meters(15.0),
        turns=400,
        wire_awg=22,
    )
    assert calculate_secondary(inp).coil_geometry == CoilGeometry.INVERSE_CONICAL


def test_secondary_height_validation():
    with pytest.raises(ValidationError):
        SecondaryInput(radius_1=0.05, radius_2=0.05, height_1=0.5, height_2=0.4, turns=300, wire_awg=22)


def test_secondary_rejects_gauges_missing_from_the_wire_table():
    with pytest.raises(ValidationError):
        SecondaryInput(radius_1=0.05, radius_2=0.05, height_1=0.0, height_2=0.4, turns=300, wire_awg=23)


def test_secondary_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        SecondaryInput(
            radius_1=0.05, radius_2=0.05, height_1=0.0, height_2=0.4, turns=300, wire_awg=22, turn=3
        )
