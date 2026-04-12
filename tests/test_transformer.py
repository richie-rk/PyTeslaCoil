"""Transformer module tests."""

import math

import pytest

from pyteslacoil.engine.transformer import LTR_FACTOR, calculate_transformer
from pyteslacoil.models.coil_design import TransformerType
from pyteslacoil.models.transformer_model import TransformerInput


def test_nst_15_60():
    """A 15 kV / 60 mA NST."""
    inp = TransformerInput(
        transformer_type=TransformerType.NST,
        input_voltage=120.0,
        output_voltage=15_000.0,
        output_current=0.060,
        line_frequency_hz=60.0,
    )
    out = calculate_transformer(inp)

    assert out.va_rating == pytest.approx(900.0, rel=1e-9)
    assert out.output_voltage_peak == pytest.approx(15_000 * math.sqrt(2), rel=1e-9)
    assert out.impedance_ohms == pytest.approx(15_000 / 0.060, rel=1e-9)
    assert out.resonant_cap_size_f > 0
    assert out.ltr_cap_size_f == pytest.approx(out.resonant_cap_size_f * LTR_FACTOR)


def test_resonant_cap_formula():
    """C_res = 1 / (2π · f · Z)."""
    inp = TransformerInput(
        input_voltage=120.0,
        output_voltage=10_000.0,
        output_current=0.050,
        line_frequency_hz=60.0,
    )
    out = calculate_transformer(inp)
    expected = 1.0 / (2 * math.pi * 60 * 200_000.0)
    assert out.resonant_cap_size_f == pytest.approx(expected, rel=1e-9)
