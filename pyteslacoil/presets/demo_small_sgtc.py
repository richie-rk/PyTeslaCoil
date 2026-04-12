"""Small SGTC preset — modeled on the Hackaday Mini SGTC build.

Reference: https://hackaday.io/project/182677
"""

from pyteslacoil.models.coil_design import (
    CoilDesign,
    ToploadType,
    TransformerType,
    UnitSystem,
)
from pyteslacoil.models.environment_model import EnvironmentInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.models.spark_gap_model import StaticGapInput
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.models.transformer_model import TransformerInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def build() -> CoilDesign:
    return CoilDesign(
        name="Small SGTC (Hackaday Mini)",
        unit_system=UnitSystem.INCHES,
        secondary=SecondaryInput(
            radius_1=inches_to_meters(0.83),
            radius_2=inches_to_meters(0.83),
            height_1=inches_to_meters(3.5),
            height_2=inches_to_meters(8.5),
            turns=570,
            wire_awg=32,
        ),
        primary=PrimaryInput(
            radius_1=inches_to_meters(1.5),
            radius_2=inches_to_meters(1.5),
            height_1=inches_to_meters(2.83),
            height_2=inches_to_meters(3.368),
            turns=11.0339,
            wire_diameter=inches_to_meters(0.0253),
            capacitance=nf_to_farads(1.3),
        ),
        topload=ToploadInput(
            topload_type=ToploadType.TOROID,
            major_diameter=inches_to_meters(4.0),
            minor_diameter=inches_to_meters(1.0),
            height=inches_to_meters(9.0),
        ),
        transformer=TransformerInput(
            transformer_type=TransformerType.NST,
            input_voltage=120.0,
            output_voltage=9_000.0,
            output_current=0.030,
        ),
        static_gap=StaticGapInput(
            num_electrodes=3,
            electrode_diameter=inches_to_meters(0.5),
            total_gap_spacing=inches_to_meters(0.10),
            transformer_voltage_peak=9_000.0 * 1.4142,
            tank_capacitance=nf_to_farads(1.3),
        ),
        environment=EnvironmentInput(),
        desired_coupling=0.16,
    )
