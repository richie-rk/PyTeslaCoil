"""Pydantic models for the secondary coil module.

All length fields are stored in **meters** (SI). Use the helpers in
:mod:`pyteslacoil.units` to convert from user-facing inches/cm.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pyteslacoil.models.coil_design import CoilGeometry


class SecondaryInput(BaseModel):

    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    radius_1: float = Field(..., gt=0, description="Bottom radius (m)")
    radius_2: float = Field(..., gt=0, description="Top radius (m)")
    height_1: float = Field(..., ge=0, description="Winding start height above ground (m)")
    height_2: float = Field(..., gt=0, description="Winding end height above ground (m)")
    turns: int = Field(..., gt=0, description="Number of turns")
    wire_awg: int = Field(..., ge=4, le=44, description="Wire gauge (AWG)")
    temperature_c: float = Field(default=20.0, description="Ambient temperature (°C)")

    @model_validator(mode="after")
    def _check_height_order(self) -> "SecondaryInput":
        if self.height_2 <= self.height_1:
            raise ValueError("height_2 must be greater than height_1")
        return self


class SecondaryOutput(BaseModel):

    model_config = ConfigDict(extra="ignore")

    inductance_h: float
    inductance_uh: float
    inductance_mh: float

    self_capacitance_f: float
    self_capacitance_pf: float

    resonant_frequency_hz: float
    resonant_frequency_khz: float

    wire_length_m: float
    wire_length_ft: float

    dc_resistance_ohms: float
    ac_resistance_ohms: float
    skin_depth_m: float

    q_factor: float
    impedance_ohms: float

    winding_height_m: float
    aspect_ratio: float
    wire_spacing_m: float

    coil_geometry: CoilGeometry

    # Optional — populated by the system-level calculator if a topload is
    # present, so the secondary's "with topload" frequency can be reported
    # in the same object.
    system_capacitance_pf: float | None = None
    system_resonant_frequency_khz: float | None = None
