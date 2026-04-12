"""Pydantic v2 data models for PyTeslaCoil.

All public engine functions take and return models defined in this package.
This makes the engine self-documenting, validates user input at the
boundary, and gives the NiceGUI frontend a typed reactive state object.
"""

from pyteslacoil.models.coil_design import (
    CoilDesign,
    CoilGeometry,
    ConductorType,
    FullSystemOutput,
    PrimaryGeometry,
    ToploadType,
    UnitSystem,
)
from pyteslacoil.models.coupling_model import CouplingInput, CouplingOutput
from pyteslacoil.models.environment_model import (
    EnvironmentInput,
    EnvironmentOutput,
)
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput
from pyteslacoil.models.secondary_model import SecondaryInput, SecondaryOutput
from pyteslacoil.models.spark_gap_model import (
    RotaryGapInput,
    RotaryGapOutput,
    StaticGapInput,
    StaticGapOutput,
)
from pyteslacoil.models.topload_model import ToploadInput, ToploadOutput
from pyteslacoil.models.transformer_model import (
    TransformerInput,
    TransformerOutput,
)

__all__ = [
    # design enums / shared
    "UnitSystem",
    "CoilGeometry",
    "PrimaryGeometry",
    "ConductorType",
    "ToploadType",
    "CoilDesign",
    "FullSystemOutput",
    # secondary
    "SecondaryInput",
    "SecondaryOutput",
    # primary
    "PrimaryInput",
    "PrimaryOutput",
    # topload
    "ToploadInput",
    "ToploadOutput",
    # coupling
    "CouplingInput",
    "CouplingOutput",
    # spark gap
    "StaticGapInput",
    "StaticGapOutput",
    "RotaryGapInput",
    "RotaryGapOutput",
    # transformer
    "TransformerInput",
    "TransformerOutput",
    # environment
    "EnvironmentInput",
    "EnvironmentOutput",
]
