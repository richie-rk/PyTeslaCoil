from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StaticGapInput(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    num_electrodes: int = Field(..., ge=2, description="Number of series electrodes")
    electrode_diameter: float = Field(..., gt=0, description="Electrode diameter (m)")
    total_gap_spacing: float = Field(..., gt=0, description="Total gap distance (m)")

    transformer_voltage_peak: float = Field(..., gt=0, description="Peak transformer voltage (V)")
    tank_capacitance: float = Field(..., gt=0, description="Tank capacitance (F)")
    line_frequency_hz: float = Field(default=60.0, gt=0)


class StaticGapOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    gap_per_electrode_m: float
    breakdown_voltage_v: float
    arc_voltage_v: float
    voltage_gradient_v_per_m: float
    arc_voltage_per_unit_v_per_m: float

    percent_cap_charged: float
    time_to_arc_s: float
    bps: float
    effective_cap_energy_j: float
    terminal_voltage_v: float
    spark_length_m: float


class RotaryGapInput(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)

    num_stationary_electrodes: int = Field(..., ge=1)
    num_rotating_electrodes: int = Field(..., ge=1)
    disc_rpm: float = Field(..., gt=0)
    rotating_electrode_diameter: float = Field(..., gt=0)
    stationary_electrode_diameter: float = Field(..., gt=0)
    rotating_path_diameter: float = Field(..., gt=0)

    transformer_voltage_peak: float = Field(..., gt=0)
    tank_capacitance: float = Field(..., gt=0)
    line_frequency_hz: float = Field(default=60.0, gt=0)


class RotaryGapOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    presentations_per_revolution: int
    bps: float
    rotational_speed_m_per_s: float
    firing_rate_s: float
    mechanical_dwell_time_s: float
    percent_cap_charged: float
    effective_cap_energy_j: float
    terminal_voltage_v: float
    spark_length_m: float
