"""Tests for the per-tab UI state object (no browser needed)."""

import logging

import pytest
from pydantic import ValidationError

from pyteslacoil.models import CoilDesign, UnitSystem
from pyteslacoil.presets import load_preset
from pyteslacoil.ui import state as state_module
from pyteslacoil.ui.defaults import default_design
from pyteslacoil.ui.state import AppState


def test_recalculate_never_modifies_the_design():
    state = AppState(load_preset("small_sgtc").model_copy(update={"auto_tune": True}))
    before = state.design.model_dump()
    state.recalculate()
    assert state.design.model_dump() == before
    assert state.outputs.tuned_primary is not None
    assert state.error is None


def test_replace_design_rebuilds_inputs_before_refreshing_results():
    state = AppState(default_design())
    calls: list[str] = []
    state.on_design_replaced(lambda s: calls.append(f"inputs:{s.design.name}"))
    state.subscribe(lambda s: calls.append(f"results:{s.outputs.secondary is not None}"))
    state.replace_design(load_preset("medium_sgtc"))
    assert calls == ["inputs:Medium SGTC (TCML reference)", "results:True"]


def test_set_section_validates_and_recalculates():
    state = AppState(default_design())
    results: list[float] = []
    state.subscribe(lambda s: results.append(s.outputs.secondary.inductance_h))
    state.set_section("secondary", load_preset("small_sgtc").secondary)
    assert results and results[-1] == pytest.approx(3.905e-3, rel=1e-3)
    with pytest.raises(ValidationError):
        state.set_section("secondary", "not a secondary")


def test_set_unit_system_rebuilds_inputs_only_on_change():
    state = AppState(default_design())
    rebuilt: list[UnitSystem] = []
    state.on_design_replaced(lambda s: rebuilt.append(s.design.unit_system))
    state.set_unit_system(UnitSystem.INCHES)
    state.set_unit_system(UnitSystem.CM)
    assert rebuilt == [UnitSystem.CM]


def test_a_failing_listener_does_not_stop_the_others(caplog):
    state = AppState(default_design())
    seen: list[bool] = []

    def broken(_state: AppState) -> None:
        raise RuntimeError("boom")

    state.subscribe(broken)
    state.subscribe(lambda _s: seen.append(True))
    with caplog.at_level(logging.ERROR):
        state.recalculate()
    assert seen == [True]
    assert "boom" in caplog.text


def test_calculation_errors_are_reported(monkeypatch):
    def failing(_design: CoilDesign):
        raise ValueError("bad design")

    monkeypatch.setattr(state_module, "calculate_system", failing)
    state = AppState(default_design())
    state.recalculate()
    assert state.error == "Calculation failed: bad design"
    assert state.outputs.secondary is None
