"""Transformer tab: the mains transformer that charges the tank capacitor."""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.engine.transformer import LTR_FACTOR
from pyteslacoil.models import TransformerInput, TransformerType
from pyteslacoil.ui.components.cards import clear_rows, result_rows, results_grid, section_card
from pyteslacoil.ui.components.inputs import ErrorLabel, number_input, on_change, value_of
from pyteslacoil.ui.defaults import default_transformer
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import TAB_ROW_CLASS

TYPES = {
    TransformerType.NST: "NST",
    TransformerType.OBIT: "OBIT",
    TransformerType.MOT: "MOT",
    TransformerType.POLE_PIG: "Pole Pig",
    TransformerType.OTHER: "Other",
}


def _inputs(state: AppState) -> None:
    xfmr = state.design.transformer or default_transformer()

    enabled = ui.switch("Mains transformer (spark-gap coil)", value=state.design.transformer is not None)
    kind = ui.select(TYPES, value=xfmr.transformer_type, label="Type").classes("w-full")
    vin = number_input("Input voltage (V_rms)", xfmr.input_voltage, step=10, decimals=1)
    vout = number_input("Output voltage (V_rms)", xfmr.output_voltage, step=100, decimals=0)
    iout = number_input("Output current (mA_rms)", xfmr.output_current * 1000, step=1, decimals=1)
    fline = number_input("Line frequency (Hz)", xfmr.line_frequency_hz, step=10, decimals=0)
    for widget in (kind, vin, vout, iout, fline):
        widget.bind_enabled_from(enabled, "value")
    errors = ErrorLabel()

    def apply() -> None:
        if not enabled.value:
            errors.clear()
            state.set_section("transformer", None)
            return
        try:
            new = TransformerInput(
                transformer_type=kind.value,
                input_voltage=value_of(vin),
                output_voltage=value_of(vout),
                output_current=value_of(iout) / 1000.0,
                line_frequency_hz=value_of(fline),
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("transformer", new)

    on_change((enabled, kind, vin, vout, iout, fline), apply)


def render(state: AppState) -> None:
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Transformer", "electric_bolt"):
                inputs = ui.refreshable(_inputs)
                inputs(state)

        with ui.column().classes("flex-1 sm:min-w-[300px]"):
            with section_card("Results", "assessment"):
                rows = result_rows(
                    results_grid(),
                    {
                        "vp": "V_peak",
                        "va": "VA rating",
                        "z": "Impedance",
                        "cres": "Resonant cap",
                        "cltr": f"LTR cap ({LTR_FACTOR:g}×)",
                        "p": "Input power (PF = 1)",
                        "i": "Input current",
                    },
                )

    def refresh(s: AppState) -> None:
        out = s.outputs.transformer
        if out is None:
            clear_rows(rows)
            return
        rows["vp"].text = f"{out.output_voltage_peak / 1000:.2f} kV"
        rows["va"].text = f"{out.va_rating:.0f} VA"
        rows["z"].text = f"{out.impedance_ohms:,.0f} Ω"
        rows["cres"].text = f"{out.resonant_cap_size_nf:.2f} nF"
        rows["cltr"].text = f"{out.ltr_cap_size_nf:.2f} nF"
        rows["p"].text = f"{out.input_power_w:.0f} W"
        rows["i"].text = f"{out.input_current_a:.2f} A"

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
