"""Pydantic models for the coupling module (SI units throughout)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field

from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput


class CouplingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    primary: PrimaryInput
    secondary: SecondaryInput
    desired_k: float | None = Field(
        default=None,
        gt=0.0,
        lt=1.0,
        description="Optional desired coupling coefficient for auto-adjust.",
    )
    auto_adjust_height: bool = Field(
        default=False,
        description="If true, the primary is shifted vertically to match desired_k.",
    )


class CouplingOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    mutual_inductance_h: float
    coupling_coefficient: float
    energy_transfer_time_s: float | None = Field(
        default=None, description="Time for a full primary→secondary transfer; None if k = 0"
    )
    energy_transfer_cycles: float | None = Field(
        default=None, description="RF cycles for a full transfer, 1/(2k); None if k = 0"
    )

    primary_inductance_h: float
    secondary_inductance_h: float

    adjusted_primary_height_1_m: float | None = None
    adjusted_primary_height_2_m: float | None = None
    adjustment_converged: bool | None = Field(
        default=None, description="Result of the height auto-adjust; None if it was not requested"
    )

    @computed_field
    @property
    def mutual_inductance_uh(self) -> float:
        return self.mutual_inductance_h * 1e6
