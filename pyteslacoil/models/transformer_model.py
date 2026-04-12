from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from pyteslacoil.models.coil_design import TransformerType


class TransformerInput(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    transformer_type: TransformerType = TransformerType.NST
    input_voltage: float = Field(..., gt=0, description="Mains voltage (V_rms)")
    output_voltage: float = Field(..., gt=0, description="Secondary voltage (V_rms)")
    output_current: float = Field(..., gt=0, description="Secondary current (A_rms)")
    line_frequency_hz: float = Field(default=60.0, gt=0)


class TransformerOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    output_voltage_peak: float
    va_rating: float
    impedance_ohms: float
    max_charging_current_a: float
    resonant_cap_size_f: float
    resonant_cap_size_nf: float
    ltr_cap_size_f: float
    ltr_cap_size_nf: float
    input_power_w: float
