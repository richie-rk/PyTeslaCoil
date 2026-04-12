"""Primary coil engine tests."""

import pytest

from pyteslacoil.engine.primary import (
    calculate_primary,
    lead_inductance,
    wheeler_helical_inductance,
    wheeler_pancake_inductance,
)
from pyteslacoil.models.coil_design import PrimaryGeometry
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.units import inches_to_meters, uf_to_farads


def test_pancake_inductance_positive():
    L = wheeler_pancake_inductance(10, 0.05, 0.20)
    assert L > 0


def test_helical_inductance_positive():
    L = wheeler_helical_inductance(10, 0.05, 0.20)
    assert L > 0


def test_lead_inductance_positive():
    L = lead_inductance(0.5, 0.005)
    assert L > 0
    assert L < 1e-6  # under a microhenry


def test_primary_flat_spiral_detected():
    inp = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(8.0),
        height_1=0.0,
        height_2=0.0,
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    out = calculate_primary(inp)
    assert out.primary_geometry == PrimaryGeometry.FLAT_SPIRAL
    assert out.inductance_h > 0
    assert out.resonant_frequency_hz > 0


def test_primary_helical_detected():
    inp = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(6.0),
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    out = calculate_primary(inp)
    assert out.primary_geometry == PrimaryGeometry.HELICAL


def test_primary_conical_detected():
    inp = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(8.0),
        height_1=0.0,
        height_2=inches_to_meters(4.0),
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    out = calculate_primary(inp)
    assert out.primary_geometry == PrimaryGeometry.CONICAL
    assert out.inductance_h > 0


def test_primary_resonance_inverse_l():
    """Larger L → lower f. Sanity check that the resonant freq formula
    behaves as expected for the helical case."""
    base = PrimaryInput(
        radius_1=inches_to_meters(3.0),
        radius_2=inches_to_meters(3.0),
        height_1=0.0,
        height_2=inches_to_meters(6.0),
        turns=5.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=uf_to_farads(0.01),
    )
    more_turns = base.model_copy(update={"turns": 20.0})
    f1 = calculate_primary(base).resonant_frequency_hz
    f2 = calculate_primary(more_turns).resonant_frequency_hz
    assert f2 < f1
