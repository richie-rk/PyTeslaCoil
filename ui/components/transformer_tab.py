from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import TransformerType
from pyteslacoil.models.transformer_model import TransformerInput
from ui.components.cards import result_row, results_grid, section_card
from ui.state import AppState


def _default_transformer() -> TransformerInput:
    return TransformerInput(
        transformer_type=TransformerType.NST,
        input_voltage=120.0,
        output_voltage=15_000.0,
        output_current=0.060,
        line_frequency_hz=60.0,
    )


def render(state: AppState) -> None:
    if state.design.transformer is None:
        state.design.transformer = _default_transformer()
    xfmr = state.design.transformer

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap"):
        # ── Inputs ─────────────────────────────────────────────────
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Transformer", "electric_bolt"):
                t_select = ui.select(
                    {
                        TransformerType.NST: "NST",
                        TransformerType.OBIT: "OBIT",
                        TransformerType.MOT: "MOT",
                        TransformerType.POLE_PIG: "Pole Pig",
                        TransformerType.OTHER: "Other",
                    },
                    value=xfmr.transformer_type,
                    label="Type",
                ).classes("w-full")

                vin = ui.number(
                    label="Input voltage (V_rms)",
                    value=xfmr.input_voltage,
                    step=10,
                    format="%.1f",
                ).classes("w-full")
                vout = ui.number(
                    label="Output voltage (V_rms)",
                    value=xfmr.output_voltage,
                    step=100,
                    format="%.0f",
                ).classes("w-full")
                iout = ui.number(
                    label="Output current (mA_rms)",
                    value=xfmr.output_current * 1000,
                    step=1,
                    format="%.1f",
                ).classes("w-full")
                fline = ui.number(
                    label="Line frequency (Hz)",
                    value=xfmr.line_frequency_hz,
                    step=10,
                    format="%.0f",
                ).classes("w-full")

                def _apply():
                    try:
                        new = TransformerInput(
                            transformer_type=t_select.value,
                            input_voltage=float(vin.value),
                            output_voltage=float(vout.value),
                            output_current=float(iout.value) / 1000.0,
                            line_frequency_hz=float(fline.value),
                        )
                    except Exception as exc:
                        ui.notify(f"Invalid input: {exc}", type="warning")
                        return
                    state.design.transformer = new
                    state.recalculate()

                for w in (vin, vout, iout, fline):
                    w.on("update:model-value", lambda *_: _apply(), throttle=0.3)
                t_select.on_value_change(lambda *_: _apply())

        # ── Results ────────────────────────────────────────────────
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Results", "assessment"):
                grid = results_grid()
                lbl_vp = result_row(grid, "V_peak")
                lbl_va = result_row(grid, "VA rating")
                lbl_z = result_row(grid, "Impedance")
                lbl_cres = result_row(grid, "Resonant cap")
                lbl_cltr = result_row(grid, "LTR cap (1.6x)")
                lbl_p = result_row(grid, "Input power")

            def _refresh(_state: AppState):
                out = _state.outputs.transformer
                if out is None:
                    return
                lbl_vp.text = f"{out.output_voltage_peak / 1000:.2f} kV"
                lbl_va.text = f"{out.va_rating:.0f} VA"
                lbl_z.text = f"{out.impedance_ohms:,.0f} \u03a9"
                lbl_cres.text = f"{out.resonant_cap_size_nf:.2f} nF"
                lbl_cltr.text = f"{out.ltr_cap_size_nf:.2f} nF"
                lbl_p.text = f"{out.input_power_w:.0f} W"

            state.subscribe(_refresh)
            state.recalculate()
