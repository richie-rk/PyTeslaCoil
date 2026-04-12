from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pyteslacoil.models.coil_design import ToploadType


class ToploadInput(BaseModel):

    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    topload_type: ToploadType = ToploadType.TOROID
    major_diameter: Optional[float] = Field(
        default=None, gt=0, description="Toroid major (outer) diameter (m)"
    )
    minor_diameter: Optional[float] = Field(
        default=None, gt=0, description="Toroid minor (tube) diameter (m)"
    )
    sphere_diameter: Optional[float] = Field(
        default=None, gt=0, description="Sphere diameter (m)"
    )
    height: float = Field(..., gt=0, description="Height above ground plane (m)")

    @model_validator(mode="after")
    def _check_dimensions(self) -> "ToploadInput":
        if self.topload_type == ToploadType.TOROID:
            if self.major_diameter is None or self.minor_diameter is None:
                raise ValueError(
                    "Toroid topload requires both major_diameter and minor_diameter."
                )
            if self.minor_diameter >= self.major_diameter:
                raise ValueError(
                    "Toroid minor_diameter must be smaller than major_diameter."
                )
        elif self.topload_type == ToploadType.SPHERE:
            if self.sphere_diameter is None:
                raise ValueError("Sphere topload requires sphere_diameter.")
        return self


class ToploadOutput(BaseModel):

    model_config = ConfigDict(extra="ignore")

    capacitance_f: float
    capacitance_pf: float
    topload_type: ToploadType
