from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from pyteslacoil.models.coil_design import ConductorType, PrimaryGeometry


class PrimaryInput(BaseModel):

    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    radius_1: float = Field(..., gt=0, description="Inner radius (m)")
    radius_2: float = Field(..., gt=0, description="Outer radius (m)")
    height_1: float = Field(..., ge=0, description="Start height (m)")
    height_2: float = Field(..., ge=0, description="End height (m)")
    turns: float = Field(..., gt=0, description="Number of turns (fractional ok)")

    wire_diameter: float = Field(..., gt=0, description="Conductor outer diameter (m)")
    capacitance: float = Field(..., gt=0, description="Tank capacitance (F)")

    lead_length: float = Field(default=0.762, ge=0, description="Lead wire length (m)")
    lead_diameter: float = Field(default=0.00508, gt=0, description="Lead wire diameter (m)")

    conductor_type: ConductorType = ConductorType.ROUND
    ribbon_width: Optional[float] = Field(default=None, description="Ribbon width (m)")
    ribbon_thickness: Optional[float] = Field(default=None, description="Ribbon thickness (m)")


class PrimaryOutput(BaseModel):

    model_config = ConfigDict(extra="ignore")

    inductance_h: float
    inductance_uh: float
    lead_inductance_h: float
    lead_inductance_uh: float
    total_inductance_h: float
    total_inductance_uh: float

    resonant_frequency_hz: float
    resonant_frequency_khz: float
    impedance_ohms: float
    dc_resistance_ohms: float
    wire_length_m: float
    wire_length_ft: float

    primary_geometry: PrimaryGeometry
    tuning_ratio: Optional[float] = None  # f_sec / f_pri
