"""Input transformer (NST/OBIT/MOT/pole-pig) calculations.

Computes peak voltage, VA rating, internal impedance, and the resonant /
LTR ("larger than resonant") tank capacitance.
"""

from __future__ import annotations

import math

from pyteslacoil.constants import PI
from pyteslacoil.models.transformer_model import TransformerInput, TransformerOutput

LTR_FACTOR: float = 1.6
"""LTR cap is conventionally ~1.6× the resonant cap value for spark-gap coils."""


def calculate_transformer(inp: TransformerInput) -> TransformerOutput:
    """Peak voltage, VA rating, impedance and recommended tank capacitance.

    The transformer is modelled as a current-limited source with impedance
    ``V_out / I_out``; the resonant capacitor matches that impedance at the
    line frequency, ``C = 1 / (2π f Z)``. Input power assumes unity power
    factor (a power-factor-corrected supply), so it equals the VA rating.
    """
    va = inp.output_voltage * inp.output_current
    impedance = inp.output_voltage / inp.output_current
    c_res = 1.0 / (2.0 * PI * inp.line_frequency_hz * impedance)

    return TransformerOutput(
        output_voltage_peak=inp.output_voltage * math.sqrt(2.0),
        va_rating=va,
        impedance_ohms=impedance,
        max_charging_current_a=inp.output_current * math.sqrt(2.0),
        resonant_cap_size_f=c_res,
        ltr_cap_size_f=c_res * LTR_FACTOR,
        input_power_w=va,
        input_current_a=va / inp.input_voltage,
    )
