"""Comparison against JavaTC reference runs (tests/fixtures/javatc_reference.json).

Expected values that have not been filled in yet (null) are skipped, so the
harness is ready for real JavaTC numbers without failing in the meantime.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pyteslacoil import calculate_system
from pyteslacoil.models import (
    CoilDesign,
    FullSystemOutput,
    PrimaryInput,
    SecondaryInput,
    ToploadInput,
    ToploadType,
)
from pyteslacoil.units import inches_to_meters, uf_to_farads

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "javatc_reference.json").read_text())

OUTPUTS: dict[str, Callable[[FullSystemOutput], float | None]] = {
    "secondary_resonant_freq_khz": lambda o: o.secondary.resonant_frequency_khz if o.secondary else None,
    "secondary_inductance_mh": lambda o: o.secondary.inductance_mh if o.secondary else None,
    "secondary_self_capacitance_pf": lambda o: o.secondary.self_capacitance_pf if o.secondary else None,
    "system_resonant_freq_khz": lambda o: o.system_resonant_frequency_khz,
    "primary_resonant_freq_khz": lambda o: o.primary.resonant_frequency_khz if o.primary else None,
    "coupling_coefficient": lambda o: o.coupling.coupling_coefficient if o.coupling else None,
}


def _design(inputs: dict[str, Any]) -> CoilDesign:
    sec, pri, top = inputs["secondary"], inputs["primary"], inputs["topload"]
    return CoilDesign(
        secondary=SecondaryInput(
            radius_1=inches_to_meters(sec["radius"]),
            radius_2=inches_to_meters(sec["radius"]),
            height_1=inches_to_meters(sec["height_1"]),
            height_2=inches_to_meters(sec["height_2"]),
            turns=sec["turns"],
            wire_awg=sec["wire_awg"],
        ),
        primary=PrimaryInput(
            radius_1=inches_to_meters(pri["radius_1"]),
            radius_2=inches_to_meters(pri["radius_2"]),
            height_1=inches_to_meters(pri["height_1"]),
            height_2=inches_to_meters(pri["height_2"]),
            turns=pri["turns"],
            wire_diameter=inches_to_meters(pri["wire_diameter"]),
            capacitance=uf_to_farads(pri["capacitance_uf"]),
        ),
        topload=ToploadInput(
            topload_type=ToploadType(top["type"]),
            major_diameter=inches_to_meters(top["major_diameter"]),
            minor_diameter=inches_to_meters(top["minor_diameter"]),
            height=inches_to_meters(top["height"]),
        ),
    )


CASES = FIXTURE["test_cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_fixture_inputs_are_valid_designs(case):
    out = calculate_system(_design(case["inputs"]))
    assert all(getter(out) is not None for getter in OUTPUTS.values())


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_matches_javatc(case):
    expected = {k: v for k, v in case["expected_outputs"].items() if k in OUTPUTS and v is not None}
    if not expected:
        pytest.skip("no JavaTC reference values filled in for this case yet")
    tolerance = case.get("tolerance_percent", FIXTURE["tolerance_percent_default"]) / 100.0
    out = calculate_system(_design(case["inputs"]))
    for key, value in expected.items():
        assert OUTPUTS[key](out) == pytest.approx(value, rel=tolerance), key
