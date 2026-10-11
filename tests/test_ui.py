"""UI tests using NiceGUI's simulated user (no browser or server needed)."""

import asyncio
from collections.abc import Awaitable, Callable

import pytest
from nicegui import ui
from nicegui.elements.mixins.value_element import ValueElement
from nicegui.testing import User, user_simulation

from pyteslacoil.models import SparkGapType, UnitSystem
from pyteslacoil.ui.defaults import default_design
from pyteslacoil.ui.main import build_ui
from pyteslacoil.ui.state import AppState
from pyteslacoil.units import inches_to_meters


def run_app(scenario: Callable[[User, list[AppState]], Awaitable[None]]) -> list[AppState]:
    """Run ``scenario`` against the app; returns the AppState of every opened tab."""
    states: list[AppState] = []

    def root() -> None:
        state = AppState(default_design())
        states.append(state)
        build_ui(state)

    async def main() -> None:
        async with user_simulation(root=root) as user:
            await user.open("/")
            await scenario(user, states)

    asyncio.run(main())
    return states


async def settle() -> None:
    """Let deferred UI refreshes run."""
    for _ in range(5):
        await asyncio.sleep(0)


def number(user: User, label_prefix: str) -> ui.number:
    matches = [
        e
        for e in user.find(kind=ui.number).elements
        if str(e.props.get("label", "")).startswith(label_prefix)
    ]
    assert len(matches) == 1, f"expected one '{label_prefix}' input, found {len(matches)}"
    return matches[0]


def select(user: User, label: str) -> ui.select:
    matches = [e for e in user.find(kind=ui.select).elements if e.props.get("label") == label]
    assert len(matches) == 1
    return matches[0]


async def set_value(user: User, element: ValueElement, value: object) -> None:
    assert user.client is not None
    with user.client:
        element.value = value
    await settle()


async def load_small_sgtc(user: User) -> None:
    user.find("Load Demo").click()
    await user.should_see("Load a Demo Coil")
    user.find(marker="preset-small_sgtc").click()
    await settle()


def test_each_browser_tab_gets_its_own_design():
    async def scenario(user: User, states: list[AppState]) -> None:
        await set_value(user, number(user, "Number of turns"), 300)
        await user.open("/")  # a second browser tab
        assert number(user, "Number of turns").value == 711

    states = run_app(scenario)
    assert [s.design.secondary.turns for s in states] == [300, 711]


def test_loading_a_preset_refreshes_the_inputs():
    async def scenario(user: User, states: list[AppState]) -> None:
        await load_small_sgtc(user)
        assert number(user, "Bottom diameter").value == pytest.approx(1.66)
        assert number(user, "Number of turns").value == 570
        assert number(user, "Output voltage").value == 9000
        # Editing one field must not resurrect values from before the preset.
        await set_value(user, number(user, "Temperature"), 21)
        secondary = states[0].design.secondary
        assert secondary is not None
        assert secondary.radius_1 == pytest.approx(inches_to_meters(0.83))
        assert secondary.temperature_c == 21

    run_app(scenario)


def test_switching_units_relabels_and_converts_the_inputs():
    async def scenario(user: User, states: list[AppState]) -> None:
        before = states[0].design.secondary
        await set_value(user, select(user, "Units"), UnitSystem.CM)
        field = number(user, "Bottom diameter")
        assert field.props["label"] == "Bottom diameter (cm)"
        assert field.value == pytest.approx(10.795)
        assert states[0].design.secondary == before  # stored in SI, unchanged

    run_app(scenario)


def test_auto_tune_checkbox_works_after_loading_a_preset():
    async def scenario(user: User, states: list[AppState]) -> None:
        await load_small_sgtc(user)
        checkbox = next(e for e in user.find(kind=ui.checkbox).elements if e.text.startswith("Auto-tune"))
        await set_value(user, checkbox, True)
        assert states[0].design.auto_tune is True
        assert states[0].outputs.tuned_primary is not None

    run_app(scenario)


def test_invalid_input_shows_an_inline_error_and_keeps_the_design():
    async def scenario(user: User, states: list[AppState]) -> None:
        before = states[0].design.secondary
        await set_value(user, number(user, "Winding end height"), 1.0)  # below the start height
        await user.should_see("height_2 must be greater than height_1")
        assert states[0].design.secondary == before

    run_app(scenario)


def test_coupling_auto_adjust_moves_the_primary_and_its_inputs():
    async def scenario(user: User, states: list[AppState]) -> None:
        user.find("Auto-adjust primary height").click()
        await settle()
        primary, coupling = states[0].design.primary, states[0].outputs.coupling
        assert primary is not None and coupling is not None
        assert primary.height_1 >= 0.0
        assert coupling.coupling_coefficient == pytest.approx(0.18, abs=1e-3)
        start = number(user, "Start height")
        assert start.value == pytest.approx(primary.height_1 / 0.0254, abs=1e-3)

    run_app(scenario)


def test_selecting_the_rotary_gap_drives_the_results():
    async def scenario(user: User, states: list[AppState]) -> None:
        await set_value(user, select(user, "Spark gap in use"), SparkGapType.ROTARY)
        out = states[0].outputs
        assert out.active_spark_gap == SparkGapType.ROTARY
        assert out.rotary_gap is not None
        assert out.estimated_spark_length_m == pytest.approx(out.rotary_gap.spark_length_m)

    run_app(scenario)


def test_spark_gap_subtab_follows_the_gap_in_use():
    async def scenario(user: User, states: list[AppState]) -> None:
        user.find("Load Demo").click()
        await user.should_see("Load a Demo Coil")
        user.find(marker="preset-medium_sgtc").click()  # a rotary-gap coil
        await settle()
        gap_tabs = [
            e for e in user.find(kind=ui.tabs).elements if {"Static", "Rotary"} <= _tab_names(e)
        ]
        assert len(gap_tabs) == 1
        value = gap_tabs[0].value
        assert getattr(value, "props", {}).get("name", value) == "Rotary"
        await user.should_see("Not part of the design")  # the static gap is not configured

    run_app(scenario)


def _tab_names(tabs: ui.element) -> set[str]:
    return {str(child.props.get("name")) for child in tabs.default_slot.children}


def test_turning_off_the_transformer_reports_the_uncharged_gap():
    async def scenario(user: User, states: list[AppState]) -> None:
        switch = next(iter(user.find(kind=ui.switch).elements))
        await set_value(user, switch, False)
        assert states[0].design.transformer is None
        await user.should_see("Static gap not calculated")

    run_app(scenario)
