from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UnitSystem(str, Enum):
    INCHES = "inches"
    CM = "cm"


class CoilGeometry(str, Enum):
    SOLENOID = "solenoid"
    CONICAL = "conical"
    INVERSE_CONICAL = "inverse_conical"


class PrimaryGeometry(str, Enum):
    FLAT_SPIRAL = "flat_spiral"
    HELICAL = "helical"
    CONICAL = "conical"
    INVERSE_CONICAL = "inverse_conical"


class ConductorType(str, Enum):
    ROUND = "round"
    RIBBON = "ribbon"
    TUBE = "tube"


class ToploadType(str, Enum):
    TOROID = "toroid"
    SPHERE = "sphere"
    NONE = "none"


class TransformerType(str, Enum):
    NST = "NST"
    OBIT = "OBIT"
    MOT = "MOT"
    POLE_PIG = "Pole Pig"
    OTHER = "Other"


class CoilDesign(BaseModel):
    """The full reactive state of a Tesla coil design.

    This is the object the NiceGUI UI binds to. The fields below are
    intentionally optional so the UI can build it up incrementally as the
    user fills in tabs.
    """

    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    name: str = "Untitled coil"
    unit_system: UnitSystem = UnitSystem.INCHES

    secondary: Optional["SecondaryInput"] = None  # noqa: F821 forward ref
    primary: Optional["PrimaryInput"] = None  # noqa: F821
    topload: Optional["ToploadInput"] = None  # noqa: F821
    static_gap: Optional["StaticGapInput"] = None  # noqa: F821
    rotary_gap: Optional["RotaryGapInput"] = None  # noqa: F821
    transformer: Optional["TransformerInput"] = None  # noqa: F821
    environment: Optional["EnvironmentInput"] = None  # noqa: F821

    desired_coupling: float = Field(
        default=0.18,
        ge=0.0,
        le=1.0,
        description="Target coupling coefficient k.",
    )
    auto_tune: bool = Field(
        default=False,
        description="If true, primary turns are auto-computed to match secondary frequency.",
    )


class FullSystemOutput(BaseModel):
    """Aggregated outputs of an entire coil design calculation."""

    model_config = ConfigDict(extra="ignore")

    secondary: Optional["SecondaryOutput"] = None  # noqa: F821
    primary: Optional["PrimaryOutput"] = None  # noqa: F821
    topload: Optional["ToploadOutput"] = None  # noqa: F821
    coupling: Optional["CouplingOutput"] = None  # noqa: F821
    static_gap: Optional["StaticGapOutput"] = None  # noqa: F821
    rotary_gap: Optional["RotaryGapOutput"] = None  # noqa: F821
    transformer: Optional["TransformerOutput"] = None  # noqa: F821
    environment: Optional["EnvironmentOutput"] = None  # noqa: F821

    system_resonant_frequency_hz: Optional[float] = None
    system_resonant_frequency_khz: Optional[float] = None
    tuning_ratio: Optional[float] = None
    estimated_spark_length_m: Optional[float] = None
    estimated_spark_length_in: Optional[float] = None


# Resolve forward references at the end of the module.
# These imports are deliberately deferred to avoid circular imports.
from pyteslacoil.models.coupling_model import CouplingOutput  # noqa: E402
from pyteslacoil.models.environment_model import (  # noqa: E402
    EnvironmentInput,
    EnvironmentOutput,
)
from pyteslacoil.models.primary_model import (  # noqa: E402
    PrimaryInput,
    PrimaryOutput,
)
from pyteslacoil.models.secondary_model import (  # noqa: E402
    SecondaryInput,
    SecondaryOutput,
)
from pyteslacoil.models.spark_gap_model import (  # noqa: E402
    RotaryGapInput,
    RotaryGapOutput,
    StaticGapInput,
    StaticGapOutput,
)
from pyteslacoil.models.topload_model import (  # noqa: E402
    ToploadInput,
    ToploadOutput,
)
from pyteslacoil.models.transformer_model import (  # noqa: E402
    TransformerInput,
    TransformerOutput,
)

CoilDesign.model_rebuild()
FullSystemOutput.model_rebuild()
