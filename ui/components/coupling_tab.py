"""Coupling coefficient tab.

Displays computed k, allows the user to set a target k, and on demand
auto-adjusts the primary's vertical position to hit it.
"""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.engine.coupling import calculate_coupling
from pyteslacoil.models.coupling_model import CouplingInput
from ui.state import AppState
from ui.theme import (
    BAD,
    CARD_CLASS,
    GOOD,
    LABEL_CLASS,
    SECTION_TITLE_CLASS,
    VALUE_CLASS,
    WARN,
)


def _quality_color(k: float) -> str:
    if 0.10 <= k <= 0.25:
        return GOOD
    if 0.05 <= k < 0.10 or 0.25 < k <= 0.30:
        return WARN
    return BAD


def render(state: AppState) -> None:
    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Target coupling").classes(SECTION_TITLE_CLASS)
                desired = ui.number(
                    label="Desired k",
                    value=state.design.desired_coupling,
                    min=0.01,
                    max=0.5,
                    step=0.01,
                    format="%.3f",
                ).classes("w-full")
                desired.bind_value_to(state.design, "desired_coupling")

                def _do_adjust():
                    if state.design.primary is None or state.design.secondary is None:
                        ui.notify("Set primary and secondary first.", type="warning")
                        return
                    out = calculate_coupling(
                        CouplingInput(
                            primary=state.design.primary,
                            secondary=state.design.secondary,
                            desired_k=state.design.desired_coupling,
                            auto_adjust_height=True,
                        )
                    )
                    if not out.adjustment_converged:
                        ui.notify(
                            "Could not bracket the desired k — try a value "
                            "between the current min/max.",
                            type="warning",
                        )
                        return
                    new_pri = state.design.primary.model_copy(
                        update={
                            "height_1": out.adjusted_primary_height_1_m,
                            "height_2": out.adjusted_primary_height_2_m,
                        }
                    )
                    state.design.primary = new_pri
                    state.recalculate()
                    ui.notify(
                        f"Primary height adjusted to k = {out.coupling_coefficient:.3f}",
                        type="positive",
                    )

                ui.button(
                    "Auto-adjust primary height", on_click=_do_adjust
                ).props("color=cyan").classes("mt-2")

        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Computed coupling").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                def _row(name, key):
                    with grid:
                        ui.label(name).classes(LABEL_CLASS)
                        labels[key] = ui.label("—").classes(VALUE_CLASS)

                _row("Coupling coefficient k", "k")
                _row("Mutual inductance", "M")
                _row("Energy transfer time", "t")
                _row("Cycles to transfer", "cyc")
                _row("Quality", "q")

            def _refresh(_state: AppState):
                out = _state.outputs.coupling
                if out is None:
                    return
                labels["k"].text = f"{out.coupling_coefficient:.4f}"
                labels["M"].text = f"{out.mutual_inductance_uh:.3f} µH"
                t_us = out.energy_transfer_time_s * 1e6
                labels["t"].text = f"{t_us:.2f} µs"
                labels["cyc"].text = f"{out.energy_transfer_cycles:.2f}"
                color = _quality_color(out.coupling_coefficient)
                labels["q"].text = "ok" if color == GOOD else (
                    "marginal" if color == WARN else "out of range"
                )
                labels["q"].style(f"color: {color}")

            state.subscribe(_refresh)
            state.recalculate()
