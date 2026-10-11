"""Enumerations shared by the input and output models.

Kept in their own module so the individual model modules can import them
without importing :mod:`pyteslacoil.models.coil_design` (which in turn
imports every model module).
"""

from __future__ import annotations

from enum import Enum


class UnitSystem(str, Enum):
    INCHES = "inches"
    CM = "cm"


class CoilGeometry(str, Enum):
    SOLENOID = "solenoid"
    CONICAL = "conical"
    INVERSE_CONICAL = "inverse_conical"


class PrimaryGeometry(str, Enum):
    FLAT_SPIRAL = "flat_spiral"
    HELICAL = "helical"
    CONICAL = "conical"
    INVERSE_CONICAL = "inverse_conical"


class ConductorType(str, Enum):
    ROUND = "round"
    RIBBON = "ribbon"
    TUBE = "tube"


class ToploadType(str, Enum):
    TOROID = "toroid"
    SPHERE = "sphere"
    NONE = "none"


class TransformerType(str, Enum):
    NST = "NST"
    OBIT = "OBIT"
    MOT = "MOT"
    POLE_PIG = "Pole Pig"
    OTHER = "Other"


class SparkGapType(str, Enum):
    """Which switch drives the primary tank circuit."""

    STATIC = "static"
    ROTARY = "rotary"
    NONE = "none"
    """No spark gap, e.g. a solid-state (DRSSTC) driver."""
