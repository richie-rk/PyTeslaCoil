"""Pydantic models for the input transformer module (SI units)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field

from pyteslacoil.constants import DEFAULT_LINE_FREQUENCY_HZ
from pyteslacoil.models.enums import TransformerType


class TransformerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    transformer_type: TransformerType = Field(
        default=TransformerType.NST, description="Descriptive; does not change the calculation"
    )
    input_voltage: float = Field(..., gt=0, description="Mains voltage (V_rms)")
    output_voltage: float = Field(..., gt=0, description="Secondary voltage (V_rms)")
    output_current: float = Field(..., gt=0, description="Secondary current (A_rms)")
    line_frequency_hz: float = Field(default=DEFAULT_LINE_FREQUENCY_HZ, gt=0)


class TransformerOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    output_voltage_peak: float
    va_rating: float
    impedance_ohms: float
    max_charging_current_a: float
    resonant_cap_size_f: float
    ltr_cap_size_f: float
    input_power_w: float = Field(description="Input power, assuming unity power factor (W = VA)")
    input_current_a: float = Field(description="Mains current at full load (A_rms)")

    @computed_field
    @property
    def resonant_cap_size_nf(self) -> float:
        return self.resonant_cap_size_f * 1e9

    @computed_field
    @property
    def ltr_cap_size_nf(self) -> float:
        return self.ltr_cap_size_f * 1e9
