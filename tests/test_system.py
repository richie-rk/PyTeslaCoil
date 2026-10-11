"""System-level calculation tests (pyteslacoil.engine.system)."""

import pytest

from pyteslacoil import calculate_system
from pyteslacoil.engine.system import resolve_spark_gap_type
from pyteslacoil.models import (
    CoilDesign,
    EnvironmentInput,
    PrimaryInput,
    SparkGapType,
    StaticGapInput,
    ToploadInput,
    ToploadType,
)
from pyteslacoil.presets import AVAILABLE_PRESETS, load_preset
from pyteslacoil.units import inches_to_meters


@pytest.mark.parametrize("preset_id", list(AVAILABLE_PRESETS))
def test_presets_are_tuned_and_plausible(preset_id):
    out = calculate_system(load_preset(preset_id))
    assert out.warnings == []
    assert out.tuning_ratio == pytest.approx(1.0, abs=0.05)
    assert out.coupling is not None
    assert 0.05 < out.coupling.coupling_coefficient < 0.35


def test_calculation_does_not_modify_the_design():
    design = load_preset("small_sgtc").model_copy(update={"auto_tune": True})
    before = design.model_dump()
    out = calculate_system(design)
    assert design.model_dump() == before
    assert out.tuned_primary is not None
    assert out.tuned_primary.turns != design.primary.turns


def test_auto_tune_matches_the_loaded_secondary():
    design = load_preset("medium_sgtc").model_copy(update={"auto_tune": True})
    out = calculate_system(design)
    assert out.tuning_ratio == pytest.approx(1.0, rel=1e-6)
    assert out.primary.resonant_frequency_hz == pytest.approx(out.system_resonant_frequency_hz)


def test_auto_tune_failure_is_reported_not_hidden():
    design = load_preset("medium_sgtc")
    impossible = design.primary.model_copy(update={"capacitance": 1e-6, "lead_length": 20.0})
    out = calculate_system(design.model_copy(update={"auto_tune": True, "primary": impossible}))
    assert out.tuned_primary is None
    assert any("Auto-tune failed" in w for w in out.warnings)


def test_environment_lowers_the_system_frequency():
    design = load_preset("medium_sgtc")
    free = calculate_system(design)
    grounded = calculate_system(
        design.model_copy(update={"environment": EnvironmentInput(ground_plane_radius=3.0)})
    )
    assert grounded.effective_topload_capacitance_f > free.effective_topload_capacitance_f
    assert grounded.system_resonant_frequency_hz < free.system_resonant_frequency_hz


def test_spark_gap_type_inference():
    design = load_preset("small_sgtc").model_copy(update={"spark_gap_type": None})
    assert resolve_spark_gap_type(design) == SparkGapType.STATIC
    rotary_only = load_preset("medium_sgtc").model_copy(update={"spark_gap_type": None})
    assert resolve_spark_gap_type(rotary_only) == SparkGapType.ROTARY
    assert resolve_spark_gap_type(CoilDesign()) == SparkGapType.NONE


def test_spark_length_comes_from_the_selected_gap():
    medium = load_preset("medium_sgtc")
    static = StaticGapInput(
        num_electrodes=4, electrode_diameter=0.01, total_gap_spacing=inches_to_meters(0.15)
    )
    both = medium.model_copy(update={"static_gap": static})
    rotary_out = calculate_system(both.model_copy(update={"spark_gap_type": SparkGapType.ROTARY}))
    static_out = calculate_system(both.model_copy(update={"spark_gap_type": SparkGapType.STATIC}))
    assert rotary_out.estimated_spark_length_m == pytest.approx(rotary_out.rotary_gap.spark_length_m)
    assert static_out.estimated_spark_length_m == pytest.approx(static_out.static_gap.spark_length_m)
    assert rotary_out.estimated_spark_length_m != pytest.approx(static_out.estimated_spark_length_m)


def test_gaps_use_the_transformer_and_primary_values():
    design = load_preset("small_sgtc")
    out = calculate_system(design)
    expected_energy = 0.5 * design.primary.capacitance * out.static_gap.breakdown_voltage_v**2
    assert out.static_gap.effective_cap_energy_j == pytest.approx(expected_energy)
    # A stale value stored on the gap itself is reported and overridden.
    stale = design.static_gap.model_copy(update={"tank_capacitance": 5e-9})
    out = calculate_system(design.model_copy(update={"static_gap": stale}))
    assert out.static_gap.effective_cap_energy_j == pytest.approx(expected_energy)
    assert any("tank_capacitance" in w for w in out.warnings)


def test_gap_without_a_charging_voltage_is_reported():
    design = load_preset("small_sgtc").model_copy(update={"transformer": None})
    out = calculate_system(design)
    assert out.static_gap is None
    assert any("Static gap not calculated" in w for w in out.warnings)


def test_gap_that_never_fires_gives_no_sparks():
    design = load_preset("small_sgtc")
    wide = design.static_gap.model_copy(update={"total_gap_spacing": 0.05})
    out = calculate_system(design.model_copy(update={"static_gap": wide}))
    assert out.estimated_spark_length_m == 0.0
    assert any("never fires" in w for w in out.warnings)


def test_overlapping_secondary_turns_are_reported():
    design = load_preset("drsstc")
    awg30 = design.secondary.model_copy(update={"wire_awg": 30})
    out = calculate_system(design.model_copy(update={"secondary": awg30}))
    assert any("Secondary" in w for w in out.warnings)


def test_primary_intersecting_the_secondary_is_reported():
    design = load_preset("small_sgtc")
    inside = PrimaryInput(
        radius_1=inches_to_meters(0.5),
        radius_2=inches_to_meters(0.5),
        height_1=inches_to_meters(4.0),
        height_2=inches_to_meters(5.0),
        turns=5,
        wire_diameter=inches_to_meters(0.05),
        capacitance=1e-9,
    )
    out = calculate_system(design.model_copy(update={"primary": inside}))
    assert any("intersects" in w for w in out.warnings)


def test_topload_below_the_secondary_top_is_reported():
    design = load_preset("small_sgtc")
    low = design.topload.model_copy(update={"height": inches_to_meters(6.0)})
    out = calculate_system(design.model_copy(update={"topload": low}))
    assert any("topload" in w.lower() for w in out.warnings)


def test_partial_designs_compute_what_they_can():
    secondary_only = CoilDesign(secondary=load_preset("small_sgtc").secondary)
    out = calculate_system(secondary_only)
    assert out.system_resonant_frequency_hz == pytest.approx(out.secondary.resonant_frequency_hz)
    assert out.primary is None and out.coupling is None and out.estimated_spark_length_m is None
    no_topload = load_preset("small_sgtc").model_copy(
        update={"topload": ToploadInput(topload_type=ToploadType.NONE)}
    )
    out = calculate_system(no_topload)
    assert out.effective_topload_capacitance_f is None
    assert out.secondary.system_resonant_frequency_hz is None
