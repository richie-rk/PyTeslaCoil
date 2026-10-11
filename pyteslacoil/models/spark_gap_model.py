"""Pydantic models for the static and rotary spark gap modules (SI units).

The charging voltage, tank capacitance and line frequency describe the tank
circuit rather than the gap itself. They are optional here: when a gap is
part of a :class:`~pyteslacoil.models.coil_design.CoilDesign`, the system
calculator takes them from the design's transformer and primary so there is a
single source of truth. They must be set to calculate a gap on its own.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_V_PEAK_DOC = "Peak charging voltage (V); None = the design's transformer peak voltage"
_C_TANK_DOC = "Tank capacitance (F); None = the design's primary capacitance"
_F_LINE_DOC = "Line frequency (Hz); None = the design's transformer, else 60 Hz"


class StaticGapInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    num_electrodes: int = Field(..., ge=2, description="Number of series electrodes")
    electrode_diameter: float = Field(
        ...,
        gt=0,
        description="Electrode diameter (m). Descriptive only: the uniform-field "
        "breakdown fit does not depend on it.",
    )
    total_gap_spacing: float = Field(..., gt=0, description="Total gap distance (m)")

    transformer_voltage_peak: float | None = Field(default=None, gt=0, description=_V_PEAK_DOC)
    tank_capacitance: float | None = Field(default=None, gt=0, description=_C_TANK_DOC)
    line_frequency_hz: float | None = Field(default=None, gt=0, description=_F_LINE_DOC)


class StaticGapOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    gap_per_electrode_m: float
    breakdown_voltage_v: float
    arc_voltage_v: float
    voltage_gradient_v_per_m: float
    arc_voltage_per_unit_v_per_m: float

    fires: bool = Field(description="False when the breakdown voltage exceeds the peak voltage")
    percent_cap_charged: float
    time_to_arc_s: float | None = Field(description="Time from zero crossing to breakdown; None if the gap never fires")
    bps: float
    effective_cap_energy_j: float
    terminal_voltage_v: float
    spark_length_m: float


class RotaryGapInput(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    num_stationary_electrodes: int = Field(
        ...,
        ge=1,
        description="Stationary electrodes, wired as series pairs (1 = single gap to a brushed rotor)",
    )
    num_rotating_electrodes: int = Field(..., ge=1)
    disc_rpm: float = Field(..., gt=0)
    rotating_electrode_diameter: float = Field(..., gt=0)
    stationary_electrode_diameter: float = Field(..., gt=0)
    rotating_path_diameter: float = Field(..., gt=0)

    transformer_voltage_peak: float | None = Field(default=None, gt=0, description=_V_PEAK_DOC)
    tank_capacitance: float | None = Field(default=None, gt=0, description=_C_TANK_DOC)
    line_frequency_hz: float | None = Field(default=None, gt=0, description=_F_LINE_DOC)


class RotaryGapOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    presentations_per_revolution: int = Field(
        description="Rotating-electrode passes over stationary electrodes per revolution"
    )
    breaks_per_revolution: int = Field(description="Firings per revolution (series pairs fire together)")
    bps: float
    rotational_speed_m_per_s: float
    firing_period_s: float
    mechanical_dwell_time_s: float
    percent_cap_charged: float
    effective_cap_energy_j: float
    terminal_voltage_v: float
    spark_length_m: float
