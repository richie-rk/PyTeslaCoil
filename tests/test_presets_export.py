"""Tests for presets and exporters."""

import json

import pytest

from pyteslacoil import calculate_system
from pyteslacoil.export.consolidated import to_text
from pyteslacoil.export.json_export import SCHEMA_VERSION, from_json, to_json
from pyteslacoil.export.pdf_export import pdf_safe, to_pdf_bytes
from pyteslacoil.models import FullSystemOutput, UnitSystem
from pyteslacoil.presets import AVAILABLE_PRESETS, PRESETS, load_preset


@pytest.mark.parametrize("preset_id", list(AVAILABLE_PRESETS.keys()))
def test_each_preset_loads_and_calculates(preset_id):
    design = load_preset(preset_id)
    out = calculate_system(design)
    assert out.secondary is not None and out.secondary.inductance_h > 0
    assert out.primary is not None and out.primary.total_inductance_h > 0
    assert AVAILABLE_PRESETS[preset_id] == PRESETS[preset_id].label


def test_load_preset_returns_a_fresh_copy():
    first = load_preset("small_sgtc")
    first.name = "edited"
    assert load_preset("small_sgtc").name != "edited"


def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        load_preset("does_not_exist")


def test_consolidated_export_contains_design_details():
    design = load_preset("small_sgtc")
    text = to_text(design, calculate_system(design))
    assert "Small SGTC" in text
    assert "Radius (bottom / top)" in text
    assert "0.8300 / 0.8300 in" in text
    assert "Resonant frequency (with topload)" in text
    assert "LTR cap (1.6×)" in text


def test_consolidated_export_uses_the_unit_system():
    design = load_preset("medium_sgtc").model_copy(update={"unit_system": UnitSystem.CM})
    text = to_text(design, calculate_system(design))
    assert "Unit system: cm" in text
    assert "5.3975 / 5.3975 cm" in text
    assert " in\n" not in text


def test_consolidated_export_handles_missing_outputs():
    design = load_preset("drsstc")
    text = to_text(design, FullSystemOutput())
    assert "System Summary" in text
    assert "Warnings" not in text


def test_consolidated_export_lists_warnings():
    design = load_preset("small_sgtc").model_copy(update={"transformer": None})
    text = to_text(design, calculate_system(design))
    assert "Warnings" in text and "Static gap not calculated" in text


def test_json_roundtrip():
    design = load_preset("medium_sgtc")
    js = to_json(design, calculate_system(design))
    parsed = json.loads(js)
    assert parsed["schema_version"] == SCHEMA_VERSION
    assert parsed["outputs"]["secondary"]["inductance_mh"] > 0
    assert from_json(js) == design


def test_json_import_accepts_version_1_files():
    design = load_preset("small_sgtc")
    legacy = json.dumps({"design": design.model_dump(mode="json"), "outputs": None})
    assert from_json(legacy) == design


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        '{"outputs": null}',
        json.dumps({"schema_version": SCHEMA_VERSION + 1, "design": {}}),
        json.dumps({"design": {"name": "x", "bogus_field": 1}}),
    ],
)
def test_json_import_rejects_invalid_files(text):
    with pytest.raises(ValueError):
        from_json(text)


def test_pdf_export_produces_a_pdf():
    design = load_preset("medium_sgtc").model_copy(update={"name": "A" * 300})
    pdf = to_pdf_bytes(design, calculate_system(design))
    assert pdf.startswith(b"%PDF")


def test_pdf_text_is_restricted_to_the_builtin_font_encoding():
    assert pdf_safe("12.3 Ω, 5 µH, 1.6×, ±") == "12.3 ohm, 5 µH, 1.6×, ±"
    pdf_safe("≈ → ✓").encode("cp1252")  # nothing left that the PDF fonts cannot draw
