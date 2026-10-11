"""Coupling coefficient tab.

Displays computed k, allows the user to set a target k, and on demand
auto-adjusts the primary's vertical position to hit it.
"""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.engine.coupling import calculate_coupling, shift_primary
from pyteslacoil.models import CouplingInput
from pyteslacoil.ui.components.cards import (
    clear_rows,
    coupling_quality,
    fmt,
    result_rows,
    results_grid,
    section_card,
)
from pyteslacoil.ui.components.inputs import ErrorLabel, number_input, on_change, value_of
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import PRIMARY_BUTTON_STYLE, TAB_ROW_CLASS
from pyteslacoil.units import length_in, length_symbol


def _inputs(state: AppState) -> None:
    desired = number_input(
        "Desired k",
        state.design.desired_coupling,
        step=0.01,
        decimals=3,
        minimum=0.01,
        maximum=0.95,
    )
    errors = ErrorLabel()

    def apply() -> None:
        try:
            state.design.desired_coupling = value_of(desired)
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()

    on_change((desired,), apply)


def _auto_adjust(state: AppState) -> None:
    design = state.design
    if design.primary is None or design.secondary is None:
        ui.notify("Set up the primary and secondary first.", type="warning")
        return
    # Move the geometry that is actually in use (the auto-tuned tap, if enabled).
    effective = state.outputs.tuned_primary or design.primary
    out = calculate_coupling(
        CouplingInput(
            primary=effective,
            secondary=design.secondary,
            desired_k=design.desired_coupling,
            auto_adjust_height=True,
        )
    )
    if not out.adjustment_converged or out.adjusted_primary_height_1_m is None:
        ui.notify(
            f"k = {design.desired_coupling:.3f} cannot be reached by moving the primary vertically "
            "(it is kept at or above the ground plane).",
            type="warning",
        )
        return
    dz = out.adjusted_primary_height_1_m - effective.height_1
    state.apply_section("primary", shift_primary(design.primary, dz))
    unit = design.unit_system.value
    ui.notify(
        f"Primary moved {length_in(dz, unit):+.3f} {length_symbol(unit)}: "
        f"k = {out.coupling_coefficient:.3f}",
        type="positive",
    )


def render(state: AppState) -> None:
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Target Coupling", "link"):
                inputs = ui.refreshable(_inputs)
                inputs(state)
                ui.button("Auto-adjust primary height", on_click=lambda: _auto_adjust(state)).style(
                    PRIMARY_BUTTON_STYLE
                ).classes("mt-3")

        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Computed Coupling", "insights"):
                rows = result_rows(
                    results_grid(),
                    {
                        "k": "Coupling coefficient k",
                        "M": "Mutual inductance",
                        "t": "Energy transfer time",
                        "cyc": "Cycles to transfer",
                        "q": "Quality",
                    },
                )

    def refresh(s: AppState) -> None:
        out = s.outputs.coupling
        if out is None:
            clear_rows(rows)
            return
        rows["k"].text = f"{out.coupling_coefficient:.4f}"
        rows["M"].text = f"{out.mutual_inductance_uh:.3f} µH"
        t_us = None if out.energy_transfer_time_s is None else out.energy_transfer_time_s * 1e6
        rows["t"].text = fmt(t_us, ".2f", "µs")
        rows["cyc"].text = fmt(out.energy_transfer_cycles, ".2f")
        quality, color = coupling_quality(out.coupling_coefficient)
        rows["q"].text = quality
        rows["q"].style(f"color: {color} !important;")

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
