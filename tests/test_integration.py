"""End-to-end integration test running a full Tesla coil design.

This is the canonical 'small SGTC' coil from the build spec — secondary,
primary (helical), toroid topload, NST transformer, static spark gap.
"""

import pytest

from pyteslacoil import (
    auto_tune,
    calculate_coupling,
    calculate_primary,
    calculate_secondary,
    calculate_static_gap,
    calculate_topload,
    calculate_transformer,
    estimate_spark_length,
)
from pyteslacoil.models.coil_design import ToploadType, TransformerType
from pyteslacoil.models.coupling_model import CouplingInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.models.spark_gap_model import StaticGapInput
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.models.transformer_model import TransformerInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def test_full_small_sgtc_design():
    secondary = SecondaryInput(
        radius_1=inches_to_meters(0.83),
        radius_2=inches_to_meters(0.83),
        height_1=inches_to_meters(3.5),
        height_2=inches_to_meters(8.5),
        turns=570,
        wire_awg=32,
    )
    sec_out = calculate_secondary(secondary)
    assert sec_out.inductance_h > 0
    assert sec_out.resonant_frequency_hz > 0

    topload = ToploadInput(
        topload_type=ToploadType.TOROID,
        major_diameter=inches_to_meters(4.0),
        minor_diameter=inches_to_meters(1.0),
        height=inches_to_meters(9.0),
    )
    top_out = calculate_topload(topload)
    assert top_out.capacitance_pf > 0

    primary = PrimaryInput(
        radius_1=inches_to_meters(1.5),
        radius_2=inches_to_meters(1.5),
        height_1=inches_to_meters(2.83),
        height_2=inches_to_meters(3.368),
        turns=11.0339,
        wire_diameter=inches_to_meters(0.0253),
        capacitance=nf_to_farads(1.3),
    )
    pri_out = calculate_primary(primary)
    assert pri_out.inductance_h > 0
    assert pri_out.resonant_frequency_hz > 0

    coupling = calculate_coupling(
        CouplingInput(primary=primary, secondary=secondary)
    )
    assert 0.05 < coupling.coupling_coefficient < 0.40

    transformer = TransformerInput(
        transformer_type=TransformerType.NST,
        input_voltage=120.0,
        output_voltage=9_000.0,
        output_current=0.030,
    )
    xfmr_out = calculate_transformer(transformer)
    assert xfmr_out.va_rating == pytest.approx(270.0)

    gap = StaticGapInput(
        num_electrodes=3,
        electrode_diameter=inches_to_meters(0.5),
        total_gap_spacing=inches_to_meters(0.10),
        transformer_voltage_peak=xfmr_out.output_voltage_peak,
        tank_capacitance=primary.capacitance,
    )
    gap_out = calculate_static_gap(gap)
    assert gap_out.spark_length_m > 0

    L_spark = estimate_spark_length(
        input_power_watts=xfmr_out.input_power_w,
        bps=gap_out.bps,
        energy_per_bang_j=gap_out.effective_cap_energy_j,
    )
    assert L_spark > 0

    # Auto-tune sanity check.
    n_new = auto_tune(sec_out.resonant_frequency_hz, primary)
    assert n_new > 0
