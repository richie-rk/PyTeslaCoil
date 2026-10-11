"""Pydantic models for the topload module (SI units throughout)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from pyteslacoil.models.enums import ToploadType


class ToploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    topload_type: ToploadType = ToploadType.TOROID
    major_diameter: float | None = Field(
        default=None, gt=0, description="Toroid major (outer) diameter (m)"
    )
    minor_diameter: float | None = Field(
        default=None, gt=0, description="Toroid minor (tube) diameter (m)"
    )
    sphere_diameter: float | None = Field(default=None, gt=0, description="Sphere diameter (m)")
    height: float | None = Field(
        default=None,
        gt=0,
        description="Height of the topload centre above the ground plane (m); "
        "required for toroids and spheres",
    )

    @model_validator(mode="after")
    def _check_dimensions(self) -> ToploadInput:
        if self.topload_type == ToploadType.TOROID:
            if self.major_diameter is None or self.minor_diameter is None:
                raise ValueError("Toroid topload requires both major_diameter and minor_diameter.")
            if 2.0 * self.minor_diameter >= self.major_diameter:
                raise ValueError(
                    "Toroid minor_diameter must be less than half the major_diameter "
                    "(otherwise the tube closes the centre hole)."
                )
        elif self.topload_type == ToploadType.SPHERE and self.sphere_diameter is None:
            raise ValueError("Sphere topload requires sphere_diameter.")
        if self.topload_type != ToploadType.NONE and self.height is None:
            raise ValueError(f"A {self.topload_type.value} topload requires its height.")
        return self


class ToploadOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    capacitance_f: float
    topload_type: ToploadType

    @computed_field
    @property
    def capacitance_pf(self) -> float:
        return self.capacitance_f * 1e12
