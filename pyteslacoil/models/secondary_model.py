"""Pydantic models for the secondary coil module.

All length fields are stored in **meters** (SI). Use the helpers in
:mod:`pyteslacoil.units` to convert from user-facing inches/cm.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from pyteslacoil.constants import DEFAULT_TEMP_C, M_TO_FT
from pyteslacoil.models.enums import CoilGeometry
from pyteslacoil.wire_data import AVAILABLE_AWG, AWG_TABLE


class SecondaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    radius_1: float = Field(..., gt=0, description="Bottom radius (m)")
    radius_2: float = Field(..., gt=0, description="Top radius (m)")
    height_1: float = Field(..., ge=0, description="Winding start height above ground (m)")
    height_2: float = Field(..., gt=0, description="Winding end height above ground (m)")
    turns: int = Field(..., gt=0, description="Number of turns")
    wire_awg: int = Field(..., description="Wire gauge (AWG); must be in the wire table")
    temperature_c: float = Field(default=DEFAULT_TEMP_C, gt=-273.15, description="Ambient temperature (°C)")

    @field_validator("wire_awg")
    @classmethod
    def _check_awg(cls, value: int) -> int:
        if value not in AWG_TABLE:
            raise ValueError(f"AWG {value} is not in the wire table; choose one of {AVAILABLE_AWG}")
        return value

    @model_validator(mode="after")
    def _check_height_order(self) -> SecondaryInput:
        if self.height_2 <= self.height_1:
            raise ValueError("height_2 must be greater than height_1")
        return self


class SecondaryOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    inductance_h: float
    self_capacitance_f: float
    resonant_frequency_hz: float
    wire_length_m: float

    dc_resistance_ohms: float
    ac_resistance_ohms: float
    skin_depth_m: float

    q_factor: float
    impedance_ohms: float

    winding_height_m: float
    aspect_ratio: float
    wire_spacing_m: float

    coil_geometry: CoilGeometry

    # Optional — populated by the system-level calculator when a topload is
    # present, so the secondary's "with topload" frequency can be reported
    # in the same object.
    system_capacitance_f: float | None = None
    system_resonant_frequency_hz: float | None = None

    @computed_field
    @property
    def inductance_uh(self) -> float:
        return self.inductance_h * 1e6

    @computed_field
    @property
    def inductance_mh(self) -> float:
        return self.inductance_h * 1e3

    @computed_field
    @property
    def self_capacitance_pf(self) -> float:
        return self.self_capacitance_f * 1e12

    @computed_field
    @property
    def resonant_frequency_khz(self) -> float:
        return self.resonant_frequency_hz / 1e3

    @computed_field
    @property
    def wire_length_ft(self) -> float:
        return self.wire_length_m * M_TO_FT

    @computed_field
    @property
    def system_capacitance_pf(self) -> float | None:
        return None if self.system_capacitance_f is None else self.system_capacitance_f * 1e12

    @computed_field
    @property
    def system_resonant_frequency_khz(self) -> float | None:
        if self.system_resonant_frequency_hz is None:
            return None
        return self.system_resonant_frequency_hz / 1e3
