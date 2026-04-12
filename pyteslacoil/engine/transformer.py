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
    v_peak = inp.output_voltage * math.sqrt(2.0)
    va = inp.output_voltage * inp.output_current
    impedance = inp.output_voltage / inp.output_current if inp.output_current > 0 else 0.0
    max_current = inp.output_current * math.sqrt(2.0)

    if impedance > 0 and inp.line_frequency_hz > 0:
        c_res = 1.0 / (2.0 * PI * inp.line_frequency_hz * impedance)
    else:
        c_res = 0.0
    c_ltr = c_res * LTR_FACTOR

    return TransformerOutput(
        output_voltage_peak=v_peak,
        va_rating=va,
        impedance_ohms=impedance,
        max_charging_current_a=max_current,
        resonant_cap_size_f=c_res,
        resonant_cap_size_nf=c_res * 1e9,
        ltr_cap_size_f=c_ltr,
        ltr_cap_size_nf=c_ltr * 1e9,
        input_power_w=va,
    )
