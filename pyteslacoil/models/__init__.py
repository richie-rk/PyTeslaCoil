"""Pydantic v2 data models for PyTeslaCoil.

All public engine functions take and return models defined in this package.
This makes the engine self-documenting, validates user input at the
boundary, and gives the NiceGUI frontend a typed state object.

Input models reject unknown fields; output models store SI values and expose
the usual display units (µH, pF, kHz, …) as computed fields.
"""

from pyteslacoil.models.coil_design import CoilDesign, FullSystemOutput
from pyteslacoil.models.coupling_model import CouplingInput, CouplingOutput
from pyteslacoil.models.enums import (
    CoilGeometry,
    ConductorType,
    PrimaryGeometry,
    SparkGapType,
    ToploadType,
    TransformerType,
    UnitSystem,
)
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
    "TransformerType",
    "SparkGapType",
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
