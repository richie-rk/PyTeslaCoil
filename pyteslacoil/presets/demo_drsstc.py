"""Compact DRSSTC preset — high-coupling solid-state design.

DRSSTCs typically run with k around 0.20-0.30, much higher than spark
gap coils, so the conical primary starts just below the secondary base and
rises past it. There is no spark gap: a solid-state bridge drives the
primary.
"""

from pyteslacoil.models.coil_design import (
    CoilDesign,
    SparkGapType,
    ToploadType,
    UnitSystem,
)
from pyteslacoil.models.environment_model import EnvironmentInput
from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.units import inches_to_meters, nf_to_farads


def build() -> CoilDesign:
    return CoilDesign(
        name="DRSSTC (compact)",
        unit_system=UnitSystem.INCHES,
        secondary=SecondaryInput(
            radius_1=inches_to_meters(1.5),
            radius_2=inches_to_meters(1.5),
            height_1=inches_to_meters(2.0),
            height_2=inches_to_meters(12.0),
            turns=1000,
            wire_awg=32,
        ),
        primary=PrimaryInput(
            radius_1=inches_to_meters(2.25),
            radius_2=inches_to_meters(3.35),
            height_1=inches_to_meters(1.5),
            height_2=inches_to_meters(3.15),
            turns=5.5,
            wire_diameter=inches_to_meters(0.25),
            capacitance=nf_to_farads(47.0),  # MMC-style
        ),
        topload=ToploadInput(
            topload_type=ToploadType.TOROID,
            major_diameter=inches_to_meters(8.0),
            minor_diameter=inches_to_meters(2.0),
            height=inches_to_meters(13.0),
        ),
        spark_gap_type=SparkGapType.NONE,
        environment=EnvironmentInput(),
        desired_coupling=0.22,
    )
