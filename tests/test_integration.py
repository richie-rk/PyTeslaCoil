"""End-to-end integration test running a full Tesla coil design module by module.

This is the canonical 'small SGTC' coil — secondary, primary (helical),
toroid topload, NST transformer, static spark gap — computed with the
stand-alone engine functions and cross-checked against the system
calculator.
"""

import pytest

from pyteslacoil import (
    auto_tune,
    calculate_coupling,
    calculate_primary,
    calculate_secondary,
    calculate_static_gap,
    calculate_system,
    calculate_topload,
    calculate_transformer,
    estimate_spark_length,
)
from pyteslacoil.engine.resonance import resonant_frequency
from pyteslacoil.models.coupling_model import CouplingInput
from pyteslacoil.models.spark_gap_model import StaticGapInput
from pyteslacoil.presets import load_preset


def test_full_small_sgtc_design():
    design = load_preset("small_sgtc")
    assert design.secondary and design.primary and design.topload and design.transformer
    assert design.static_gap is not None

    sec_out = calculate_secondary(design.secondary)
    top_out = calculate_topload(design.topload)
    f_loaded = resonant_frequency(sec_out.inductance_h, sec_out.self_capacitance_f + top_out.capacitance_f)

    pri_out = calculate_primary(design.primary)
    assert pri_out.resonant_frequency_hz == pytest.approx(f_loaded, rel=0.01)

    coupling = calculate_coupling(CouplingInput(primary=design.primary, secondary=design.secondary))
    assert 0.05 < coupling.coupling_coefficient < 0.30

    xfmr_out = calculate_transformer(design.transformer)
    assert xfmr_out.va_rating == pytest.approx(270.0)

    gap = StaticGapInput(
        num_electrodes=design.static_gap.num_electrodes,
        electrode_diameter=design.static_gap.electrode_diameter,
        total_gap_spacing=design.static_gap.total_gap_spacing,
        transformer_voltage_peak=xfmr_out.output_voltage_peak,
        tank_capacitance=design.primary.capacitance,
    )
    gap_out = calculate_static_gap(gap)
    assert gap_out.fires and gap_out.spark_length_m > 0

    spark = estimate_spark_length(
        input_power_watts=xfmr_out.input_power_w,
        bps=gap_out.bps,
        energy_per_bang_j=gap_out.effective_cap_energy_j,
    )
    assert spark == pytest.approx(gap_out.spark_length_m)

    # The preset is already tapped at the tuned turn count.
    assert auto_tune(f_loaded, design.primary) == pytest.approx(design.primary.turns, rel=1e-3)

    # The system calculator combines the same pieces.
    system = calculate_system(design)
    assert system.system_resonant_frequency_hz == pytest.approx(f_loaded)
    assert system.coupling.coupling_coefficient == pytest.approx(coupling.coupling_coefficient)
    assert system.estimated_spark_length_m == pytest.approx(spark)
