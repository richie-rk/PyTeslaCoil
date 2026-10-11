"""Pydantic models for the primary coil module (SI units throughout)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from pyteslacoil.constants import M_TO_FT
from pyteslacoil.models.enums import ConductorType, PrimaryGeometry
from pyteslacoil.units import lengths_equal


class PrimaryInput(BaseModel):
    """Primary winding geometry and tank circuit.

    The conductor runs from ``(radius_1, height_1)`` to ``(radius_2,
    height_2)`` over ``turns`` turns: equal heights describe a flat spiral,
    equal radii a helix, and anything else a (inverse) conical winding.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    radius_1: float = Field(..., gt=0, description="Start (inner) radius (m)")
    radius_2: float = Field(..., gt=0, description="End (outer) radius (m)")
    height_1: float = Field(..., ge=0, description="Start height (m)")
    height_2: float = Field(..., ge=0, description="End height (m)")
    turns: float = Field(..., gt=0, description="Number of turns (fractional ok)")

    wire_diameter: float = Field(..., gt=0, description="Conductor outer diameter (m)")
    capacitance: float = Field(..., gt=0, description="Tank capacitance (F)")

    lead_length: float = Field(default=0.762, ge=0, description="Total lead wire length (m)")
    lead_diameter: float = Field(default=0.00508, gt=0, description="Lead wire diameter (m)")

    conductor_type: ConductorType = ConductorType.ROUND
    ribbon_width: float | None = Field(default=None, gt=0, description="Ribbon width (m)")
    ribbon_thickness: float | None = Field(default=None, gt=0, description="Ribbon thickness (m)")

    @model_validator(mode="after")
    def _check_geometry(self) -> PrimaryInput:
        if lengths_equal(self.radius_1, self.radius_2) and lengths_equal(self.height_1, self.height_2):
            raise ValueError(
                "The primary needs a radial extent (flat spiral), an axial extent "
                "(helical) or both (conical); equal radii and equal heights describe "
                "a single loop."
            )
        if self.conductor_type == ConductorType.RIBBON and (
            self.ribbon_width is None or self.ribbon_thickness is None
        ):
            raise ValueError("A ribbon conductor requires ribbon_width and ribbon_thickness.")
        return self


class PrimaryOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    inductance_h: float
    lead_inductance_h: float
    total_inductance_h: float

    resonant_frequency_hz: float
    impedance_ohms: float
    dc_resistance_ohms: float
    wire_length_m: float

    primary_geometry: PrimaryGeometry
    tuning_ratio: float | None = None  # f_sec / f_pri

    @computed_field
    @property
    def inductance_uh(self) -> float:
        return self.inductance_h * 1e6

    @computed_field
    @property
    def lead_inductance_uh(self) -> float:
        return self.lead_inductance_h * 1e6

    @computed_field
    @property
    def total_inductance_uh(self) -> float:
        return self.total_inductance_h * 1e6

    @computed_field
    @property
    def resonant_frequency_khz(self) -> float:
        return self.resonant_frequency_hz / 1e3

    @computed_field
    @property
    def wire_length_ft(self) -> float:
        return self.wire_length_m * M_TO_FT
