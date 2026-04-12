"""Tests for presets and exporters."""

import json

import pytest

from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.export.consolidated import to_text
from pyteslacoil.export.json_export import from_json, to_json
from pyteslacoil.models import FullSystemOutput
from pyteslacoil.presets import AVAILABLE_PRESETS, load_preset


@pytest.mark.parametrize("preset_id", list(AVAILABLE_PRESETS.keys()))
def test_each_preset_loads_and_calculates(preset_id):
    design = load_preset(preset_id)
    assert design.secondary is not None
    assert design.primary is not None
    sec = calculate_secondary(design.secondary)
    pri = calculate_primary(design.primary)
    assert sec.inductance_h > 0
    assert pri.total_inductance_h > 0


def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        load_preset("does_not_exist")


def test_consolidated_export_contains_design_name():
    design = load_preset("small_sgtc")
    out = FullSystemOutput(
        secondary=calculate_secondary(design.secondary),
        primary=calculate_primary(design.primary),
    )
    text = to_text(design, out)
    assert "Small SGTC" in text
    assert "Inductance" in text
    assert "Resonant frequency" in text


def test_json_roundtrip():
    design = load_preset("medium_sgtc")
    js = to_json(design)
    parsed = json.loads(js)
    assert "design" in parsed
    restored = from_json(js)
    assert restored.secondary == design.secondary
    assert restored.primary == design.primary
