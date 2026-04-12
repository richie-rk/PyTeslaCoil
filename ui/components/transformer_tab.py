from __future__ import annotations

from nicegui import ui

from pyteslacoil.models.coil_design import TransformerType
from pyteslacoil.models.transformer_model import TransformerInput
from ui.state import AppState
from ui.theme import CARD_CLASS, LABEL_CLASS, SECTION_TITLE_CLASS, VALUE_CLASS


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

    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Transformer").classes(SECTION_TITLE_CLASS)

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
                    label="Output current (A_rms)",
                    value=xfmr.output_current * 1000,  # mA for ergonomics
                    step=1,
                    format="%.1f",
                    suffix="mA",
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

        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Results").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                def _row(name, key):
                    with grid:
                        ui.label(name).classes(LABEL_CLASS)
                        labels[key] = ui.label("—").classes(VALUE_CLASS)

                _row("V_peak", "vp")
                _row("VA rating", "va")
                _row("Impedance", "z")
                _row("Resonant cap", "cres")
                _row("LTR cap (1.6×)", "cltr")
                _row("Input power", "p")

            def _refresh(_state: AppState):
                out = _state.outputs.transformer
                if out is None:
                    return
                labels["vp"].text = f"{out.output_voltage_peak / 1000:.2f} kV"
                labels["va"].text = f"{out.va_rating:.0f} VA"
                labels["z"].text = f"{out.impedance_ohms:,.0f} Ω"
                labels["cres"].text = f"{out.resonant_cap_size_nf:.2f} nF"
                labels["cltr"].text = f"{out.ltr_cap_size_nf:.2f} nF"
                labels["p"].text = f"{out.input_power_w:.0f} W"

            state.subscribe(_refresh)
            state.recalculate()
