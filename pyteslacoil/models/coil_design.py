"""Top-level design and system-output models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field

from pyteslacoil.constants import M_TO_INCH
from pyteslacoil.models.coupling_model import CouplingOutput
from pyteslacoil.models.enums import (
    CoilGeometry,
    ConductorType,
    PrimaryGeometry,
    SparkGapType,
    ToploadType,
    TransformerType,
    UnitSystem,
)
from pyteslacoil.models.environment_model import EnvironmentInput, EnvironmentOutput
from pyteslacoil.models.primary_model import PrimaryInput, PrimaryOutput
from pyteslacoil.models.secondary_model import SecondaryInput, SecondaryOutput
from pyteslacoil.models.spark_gap_model import (
    RotaryGapInput,
    RotaryGapOutput,
    StaticGapInput,
    StaticGapOutput,
)
from pyteslacoil.models.topload_model import ToploadInput, ToploadOutput
from pyteslacoil.models.transformer_model import TransformerInput, TransformerOutput

# The enums used to live in this module; keep them importable from here.
__all__ = [
    "CoilDesign",
    "CoilGeometry",
    "ConductorType",
    "FullSystemOutput",
    "PrimaryGeometry",
    "SparkGapType",
    "ToploadType",
    "TransformerType",
    "UnitSystem",
]


class CoilDesign(BaseModel):
    """The full set of inputs describing a Tesla coil design.

    The sections are optional so a design can be built up incrementally;
    :func:`pyteslacoil.engine.system.calculate_system` computes whatever the
    configured sections allow.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = "Untitled coil"
    unit_system: UnitSystem = UnitSystem.INCHES

    secondary: SecondaryInput | None = None
    primary: PrimaryInput | None = None
    topload: ToploadInput | None = None
    static_gap: StaticGapInput | None = None
    rotary_gap: RotaryGapInput | None = None
    transformer: TransformerInput | None = None
    environment: EnvironmentInput | None = None

    spark_gap_type: SparkGapType | None = Field(
        default=None,
        description="Which gap drives the coil. None = the configured gap (static if both are).",
    )
    desired_coupling: float = Field(
        default=0.18,
        gt=0.0,
        lt=1.0,
        description="Target coupling coefficient k for the height auto-adjust.",
    )
    auto_tune: bool = Field(
        default=False,
        description="If true, the primary is tapped at the turn count that matches the "
        "loaded secondary frequency.",
    )


class FullSystemOutput(BaseModel):
    """Aggregated outputs of an entire coil design calculation."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    secondary: SecondaryOutput | None = None
    primary: PrimaryOutput | None = None
    topload: ToploadOutput | None = None
    coupling: CouplingOutput | None = None
    static_gap: StaticGapOutput | None = None
    rotary_gap: RotaryGapOutput | None = None
    transformer: TransformerOutput | None = None
    environment: EnvironmentOutput | None = None

    tuned_primary: PrimaryInput | None = Field(
        default=None, description="The primary geometry selected by auto-tune, if enabled."
    )
    active_spark_gap: SparkGapType | None = None
    effective_topload_capacitance_f: float | None = Field(
        default=None, description="Topload capacitance including environment proximity effects."
    )
    system_resonant_frequency_hz: float | None = None
    tuning_ratio: float | None = None
    estimated_spark_length_m: float | None = None
    estimated_terminal_voltage_v: float | None = None
    warnings: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def system_resonant_frequency_khz(self) -> float | None:
        if self.system_resonant_frequency_hz is None:
            return None
        return self.system_resonant_frequency_hz / 1e3

    @computed_field
    @property
    def effective_topload_capacitance_pf(self) -> float | None:
        if self.effective_topload_capacitance_f is None:
            return None
        return self.effective_topload_capacitance_f * 1e12

    @computed_field
    @property
    def estimated_spark_length_in(self) -> float | None:
        if self.estimated_spark_length_m is None:
            return None
        return self.estimated_spark_length_m * M_TO_INCH
