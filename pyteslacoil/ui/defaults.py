"""Default inputs for a fresh UI session.

Tabs show these values for sections a loaded design does not have (for
example the transformer of a solid-state preset) without adding them to the
design until the user enables or edits them.
"""

from __future__ import annotations

from pyteslacoil.models import (
    CoilDesign,
    EnvironmentInput,
    PrimaryInput,
    RotaryGapInput,
    SecondaryInput,
    SparkGapType,
    StaticGapInput,
    ToploadInput,
    ToploadType,
    TransformerInput,
    TransformerType,
    UnitSystem,
)
from pyteslacoil.units import inches_to_meters, nf_to_farads


def default_secondary() -> SecondaryInput:
    return SecondaryInput(
        radius_1=inches_to_meters(2.125),
        radius_2=inches_to_meters(2.125),
        height_1=inches_to_meters(3.0),
        height_2=inches_to_meters(19.0),
        turns=711,
        wire_awg=24,
    )


def default_primary() -> PrimaryInput:
    return PrimaryInput(
        radius_1=inches_to_meters(3.5),
        radius_2=inches_to_meters(8.0),
        height_1=inches_to_meters(0.5),
        height_2=inches_to_meters(0.5),
        turns=10.0,
        wire_diameter=inches_to_meters(0.25),
        capacitance=nf_to_farads(10.0),
        lead_length=inches_to_meters(30.0),
        lead_diameter=inches_to_meters(0.2),
    )


def default_topload() -> ToploadInput:
    return ToploadInput(
        topload_type=ToploadType.TOROID,
        major_diameter=inches_to_meters(6.0),
        minor_diameter=inches_to_meters(1.5),
        height=inches_to_meters(20.0),
    )


def default_transformer() -> TransformerInput:
    return TransformerInput(
        transformer_type=TransformerType.NST,
        input_voltage=120.0,
        output_voltage=15_000.0,
        output_current=0.060,
        line_frequency_hz=60.0,
    )


def default_static_gap() -> StaticGapInput:
    return StaticGapInput(
        num_electrodes=4,
        electrode_diameter=inches_to_meters(0.5),
        total_gap_spacing=inches_to_meters(0.15),
    )


def default_rotary_gap() -> RotaryGapInput:
    return RotaryGapInput(
        num_stationary_electrodes=2,
        num_rotating_electrodes=8,
        disc_rpm=3000.0,
        rotating_electrode_diameter=inches_to_meters(0.25),
        stationary_electrode_diameter=inches_to_meters(0.25),
        rotating_path_diameter=inches_to_meters(8.0),
    )


def default_design() -> CoilDesign:
    """The design a new browser tab starts with."""
    return CoilDesign(
        unit_system=UnitSystem.INCHES,
        secondary=default_secondary(),
        primary=default_primary(),
        topload=default_topload(),
        transformer=default_transformer(),
        static_gap=default_static_gap(),
        rotary_gap=default_rotary_gap(),
        spark_gap_type=SparkGapType.STATIC,
        environment=EnvironmentInput(),
    )
