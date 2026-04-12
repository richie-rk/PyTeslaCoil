"""Pydantic models for the surrounding-environment module.

The environment affects topload capacitance via image-charge effects from
nearby ground planes, walls, and ceilings. The model is intentionally
permissive — values of 0 mean "infinitely far / not present".
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentInput(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    ground_plane_radius: float = Field(default=0.0, ge=0, description="Radius of conducting ground plane (m); 0 = infinite/none")
    wall_radius: float = Field(default=0.0, ge=0, description="Radius to nearest wall (m); 0 = walls absent")
    ceiling_height: float = Field(default=0.0, ge=0, description="Ceiling height above ground plane (m); 0 = none")


class EnvironmentOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    proximity_correction_factor: float
    notes: str
