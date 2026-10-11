"""Primary coil engine tests."""

import math

import numpy as np
import pytest
from pydantic import ValidationError

from pyteslacoil.engine.primary import (
    calculate_primary,
    conical_primary_inductance,
    filamentary_coil_inductance,
    lead_inductance,
    primary_dc_resistance,
    wheeler_helical_inductance,
    wheeler_pancake_inductance,
)
from pyteslacoil.models.coil_design import ConductorType, PrimaryGeometry
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def _primary(**overrides) -> PrimaryInput:
    data = dict(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(8.0),
        height_1=0.0,
        height_2=0.0,
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    data.update(overrides)
    return PrimaryInput(**data)


def test_pancake_matches_wheelers_inch_formula():
    """Wheeler (1928): L[µH] = r² N² / (8 r + 11 w) with r, w in inches."""
    turns, r1_in, r2_in = 10.8191, 3.75, 9.203
    r_in, w_in = 0.5 * (r1_in + r2_in), r2_in - r1_in
    reference_uh = r_in**2 * turns**2 / (8 * r_in + 11 * w_in)
    computed_uh = wheeler_pancake_inductance(
        turns, inches_to_meters(r1_in), inches_to_meters(r2_in)
    ) * 1e6
    assert computed_uh == pytest.approx(reference_uh, rel=0.005)


def test_pancake_agrees_with_independent_filament_sum():
    """The Wheeler pancake and the filamentary model describe the same coil."""
    inp = _primary(turns=12.0)
    radii = inches_to_meters(3.0) + (inches_to_meters(5.0) / 12.0) * (np.arange(12) + 0.5)
    filament_l = filamentary_coil_inductance(radii, np.zeros(12), 0.5 * inp.wire_diameter)
    assert calculate_primary(inp).inductance_h == pytest.approx(filament_l, rel=0.06)


def test_pancake_radius_order_does_not_matter():
    assert wheeler_pancake_inductance(10, 0.05, 0.20) == pytest.approx(
        wheeler_pancake_inductance(10, 0.20, 0.05)
    )


def test_helical_matches_wheelers_inch_formula():
    """Wheeler: L[µH] = r² N² / (9 r + 10 l) with r, l in inches."""
    reference_uh = 3.0**2 * 10**2 / (9 * 3.0 + 10 * 6.0)
    computed_uh = (
        wheeler_helical_inductance(10, inches_to_meters(3.0), inches_to_meters(6.0)) * 1e6
    )
    assert computed_uh == pytest.approx(reference_uh, rel=0.005)


def test_inductance_helpers_reject_invalid_dimensions():
    with pytest.raises(ValueError):
        wheeler_helical_inductance(10, 0.05, 0.0)
    with pytest.raises(ValueError):
        wheeler_pancake_inductance(10, 0.05, 0.05)


def test_lead_inductance_positive_and_never_negative():
    long_lead = lead_inductance(0.5, 0.005)
    assert 0 < long_lead < 1e-6  # under a microhenry
    assert lead_inductance(0.001, 0.005) == 0.0  # formula invalid this short: clamped
    assert lead_inductance(0.0, 0.005) == 0.0


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, PrimaryGeometry.FLAT_SPIRAL),
        ({"radius_2": inches_to_meters(3.0), "height_2": inches_to_meters(6.0)}, PrimaryGeometry.HELICAL),
        ({"height_2": inches_to_meters(4.0)}, PrimaryGeometry.CONICAL),
        (
            {"radius_1": inches_to_meters(8.0), "radius_2": inches_to_meters(3.0), "height_2": 0.1},
            PrimaryGeometry.INVERSE_CONICAL,
        ),
    ],
)
def test_geometry_detection(overrides, expected):
    out = calculate_primary(_primary(**overrides))
    assert out.primary_geometry == expected
    assert out.inductance_h > 0
    assert out.total_inductance_h == pytest.approx(out.inductance_h + out.lead_inductance_h)


def test_single_loop_primary_is_rejected():
    with pytest.raises(ValidationError):
        _primary(radius_2=inches_to_meters(3.0))


def test_ribbon_conductor_requires_dimensions():
    with pytest.raises(ValidationError):
        _primary(conductor_type=ConductorType.RIBBON)
    ribbon = _primary(
        conductor_type=ConductorType.RIBBON, ribbon_width=0.01, ribbon_thickness=0.0005
    )
    assert primary_dc_resistance(1.0, ribbon) == pytest.approx(1.7241e-8 / (0.01 * 0.0005))


def test_tube_has_more_resistance_than_solid_wire():
    solid = _primary()
    tube = _primary(conductor_type=ConductorType.TUBE)
    assert primary_dc_resistance(10.0, tube) > primary_dc_resistance(10.0, solid)


def test_conical_inductance_is_continuous_in_fractional_turns():
    """Fractional turns must not make the filament model jump between integers."""
    values = [
        conical_primary_inductance(_primary(height_2=inches_to_meters(4.0), turns=n))
        for n in np.linspace(9.6, 10.4, 9)
    ]
    steps = np.diff(values)
    assert np.all(steps > 0)
    assert steps.max() < 3.0 * steps.min()


def test_primary_resonance_inverse_l():
    """Larger L → lower f."""
    base = _primary(radius_2=inches_to_meters(3.0), height_2=inches_to_meters(6.0), turns=5.0)
    more_turns = base.model_copy(update={"turns": 20.0})
    f1 = calculate_primary(base).resonant_frequency_hz
    f2 = calculate_primary(more_turns).resonant_frequency_hz
    assert f2 < f1
    out = calculate_primary(base)
    assert out.resonant_frequency_hz == pytest.approx(
        1.0 / (2 * math.pi * math.sqrt(out.total_inductance_h * base.capacitance))
    )
