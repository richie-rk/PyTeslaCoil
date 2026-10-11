"""Pydantic models for the surrounding-environment module.

The environment raises the topload capacitance through image-charge effects
from nearby grounded surfaces. Every distance defaults to 0, which means the
surface is absent; with all three absent the topload is treated as being in
free space.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    ground_plane_radius: float = Field(
        default=0.0,
        ge=0,
        description="Radius of the grounded plane the coil stands on (m); 0 = no ground plane",
    )
    wall_radius: float = Field(
        default=0.0, ge=0, description="Distance from the coil axis to the walls (m); 0 = no walls"
    )
    ceiling_height: float = Field(
        default=0.0,
        ge=0,
        description="Ceiling height above the ground plane (m); 0 = no ceiling",
    )


class EnvironmentOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    proximity_correction_factor: float = Field(
        description="Multiplier for the free-space topload capacitance (1 = free space)"
    )
    notes: str
    warnings: list[str] = Field(default_factory=list)
