"""Coupling coefficient tab.

Displays computed k, allows the user to set a target k, and on demand
auto-adjusts the primary's vertical position to hit it.
"""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.engine.coupling import calculate_coupling
from pyteslacoil.models.coupling_model import CouplingInput
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState
from ui.theme import ACCENT, BAD, GOOD, WARN


def _quality_color(k: float) -> str:
    if 0.10 <= k <= 0.25:
        return GOOD
    if 0.05 <= k < 0.10 or 0.25 < k <= 0.30:
        return WARN
    return BAD


def render(state: AppState) -> None:
    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        # ── Inputs ─────────────────────────────────────────────────
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Target Coupling", "link"):
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
                            "Could not bracket the desired k \u2014 try a value "
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
                ).style(
                    f"background: {ACCENT}; color: #0f1117; border-radius: 6px;"
                ).classes("mt-3")

        # ── Results ────────────────────────────────────────────────
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Computed Coupling", "insights"):
                grid = results_grid()
                lbl_k = result_row(grid, "Coupling coefficient k")
                lbl_M = result_row(grid, "Mutual inductance")
                lbl_t = result_row(grid, "Energy transfer time")
                lbl_cyc = result_row(grid, "Cycles to transfer")
                lbl_q = result_row(grid, "Quality")

            def _refresh(_state: AppState):
                out = _state.outputs.coupling
                if out is None:
                    return
                lbl_k.text = f"{out.coupling_coefficient:.4f}"
                lbl_M.text = f"{out.mutual_inductance_uh:.3f} \u00b5H"
                t_us = out.energy_transfer_time_s * 1e6
                lbl_t.text = f"{t_us:.2f} \u00b5s"
                lbl_cyc.text = f"{out.energy_transfer_cycles:.2f}"
                color = _quality_color(out.coupling_coefficient)
                quality = "ok" if color == GOOD else (
                    "marginal" if color == WARN else "out of range"
                )
                lbl_q.text = quality
                lbl_q.style(f"color: {color} !important;")

            state.subscribe(_refresh)
            state.recalculate()
