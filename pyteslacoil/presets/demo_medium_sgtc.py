"""Medium SGTC preset — modeled on a typical TCML / pupman build."""

from pyteslacoil.models.coil_design import (
    CoilDesign,
    ToploadType,
    TransformerType,
    UnitSystem,
)
from pyteslacoil.models.environment_model import EnvironmentInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.models.spark_gap_model import RotaryGapInput
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.models.transformer_model import TransformerInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def build() -> CoilDesign:
    return CoilDesign(
        name="Medium SGTC (TCML reference)",
        unit_system=UnitSystem.INCHES,
        secondary=SecondaryInput(
            radius_1=inches_to_meters(2.125),
            radius_2=inches_to_meters(2.125),
            height_1=inches_to_meters(3.0),
            height_2=inches_to_meters(19.0),
            turns=711,
            wire_awg=24,
        ),
        primary=PrimaryInput(
            radius_1=inches_to_meters(3.75),
            radius_2=inches_to_meters(9.203),
            height_1=inches_to_meters(1.0),
            height_2=inches_to_meters(1.0),
            turns=10.8191,
            wire_diameter=inches_to_meters(0.25),
            capacitance=nf_to_farads(7.7),
        ),
        topload=ToploadInput(
            topload_type=ToploadType.TOROID,
            major_diameter=inches_to_meters(20.0),
            minor_diameter=inches_to_meters(4.0),
            height=inches_to_meters(21.0),
        ),
        transformer=TransformerInput(
            transformer_type=TransformerType.NST,
            input_voltage=120.0,
            output_voltage=15_000.0,
            output_current=0.060,
        ),
        rotary_gap=RotaryGapInput(
            num_stationary_electrodes=2,
            num_rotating_electrodes=8,
            disc_rpm=3000.0,
            rotating_electrode_diameter=inches_to_meters(0.25),
            stationary_electrode_diameter=inches_to_meters(0.25),
            rotating_path_diameter=inches_to_meters(8.0),
            transformer_voltage_peak=15_000.0 * 1.4142,
            tank_capacitance=nf_to_farads(7.7),
        ),
        environment=EnvironmentInput(),
        desired_coupling=0.18,
    )
