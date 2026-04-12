from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from pyteslacoil.models.primary_model import PrimaryInput
from pyteslacoil.models.secondary_model import SecondaryInput


class CouplingInput(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    primary: PrimaryInput
    secondary: SecondaryInput
    desired_k: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional desired coupling coefficient for auto-adjust.",
    )
    auto_adjust_height: bool = Field(
        default=False,
        description="If true, the primary height_1/height_2 will be shifted to match desired_k.",
    )


class CouplingOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mutual_inductance_h: float
    mutual_inductance_uh: float
    coupling_coefficient: float
    energy_transfer_time_s: float
    energy_transfer_cycles: float

    primary_inductance_h: float
    secondary_inductance_h: float

    adjusted_primary_height_1_m: Optional[float] = None
    adjusted_primary_height_2_m: Optional[float] = None
    adjustment_converged: bool = True
