"""Unit conversion utilities.

The engine works in SI (meters, henries, farads, hertz) internally. Convert
to user-facing units only at the input/output boundary.
"""

import math

from pyteslacoil.constants import FT_TO_M, INCH_TO_M, LENGTH_ABS_TOL, LENGTH_REL_TOL


# ---------------------------------------------------------------------------
# Length
# ---------------------------------------------------------------------------
def inches_to_meters(val: float) -> float:
    return val * INCH_TO_M


def meters_to_inches(val: float) -> float:
    return val / INCH_TO_M


def cm_to_meters(val: float) -> float:
    return val * 0.01


def meters_to_cm(val: float) -> float:
    return val * 100.0


def feet_to_meters(val: float) -> float:
    return val * FT_TO_M


def meters_to_feet(val: float) -> float:
    return val / FT_TO_M


def mm_to_meters(val: float) -> float:
    return val * 1e-3


def meters_to_mm(val: float) -> float:
    return val * 1e3


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------
def fahrenheit_to_celsius(val: float) -> float:
    return (val - 32.0) * 5.0 / 9.0


def celsius_to_fahrenheit(val: float) -> float:
    return val * 9.0 / 5.0 + 32.0


# ---------------------------------------------------------------------------
# Frequency
# ---------------------------------------------------------------------------
def hz_to_khz(val: float) -> float:
    return val / 1000.0


def khz_to_hz(val: float) -> float:
    return val * 1000.0


def hz_to_mhz(val: float) -> float:
    return val / 1e6


def mhz_to_hz(val: float) -> float:
    return val * 1e6


# ---------------------------------------------------------------------------
# Capacitance
# ---------------------------------------------------------------------------
def farads_to_pf(val: float) -> float:
    return val * 1e12


def pf_to_farads(val: float) -> float:
    return val * 1e-12


def farads_to_nf(val: float) -> float:
    return val * 1e9


def nf_to_farads(val: float) -> float:
    return val * 1e-9


def farads_to_uf(val: float) -> float:
    return val * 1e6


def uf_to_farads(val: float) -> float:
    return val * 1e-6


# ---------------------------------------------------------------------------
# Inductance
# ---------------------------------------------------------------------------
def henries_to_uh(val: float) -> float:
    return val * 1e6


def uh_to_henries(val: float) -> float:
    return val * 1e-6


def henries_to_mh(val: float) -> float:
    return val * 1e3


def mh_to_henries(val: float) -> float:
    return val * 1e-3


# ---------------------------------------------------------------------------
# Generic helpers for user-selectable length units.
# ---------------------------------------------------------------------------
_LENGTH_UNITS: dict[str, float] = {
    "inches": INCH_TO_M,
    "in": INCH_TO_M,
    "cm": 0.01,
    "mm": 1e-3,
    "m": 1.0,
    "meters": 1.0,
}

_LENGTH_SYMBOLS: dict[str, str] = {
    "inches": "in",
    "in": "in",
    "cm": "cm",
    "mm": "mm",
    "m": "m",
    "meters": "m",
}


def _length_factor(unit: str) -> float:
    try:
        return _LENGTH_UNITS[unit.lower()]
    except KeyError:
        raise ValueError(f"Unknown length unit: {unit!r}") from None


def length_in(value_m: float, unit: str) -> float:
    """Convert a length in meters to the requested user unit."""
    return value_m / _length_factor(unit)


def length_to_meters(value: float, unit: str) -> float:
    """Convert a user-supplied length to meters."""
    return value * _length_factor(unit)


def length_symbol(unit: str) -> str:
    """Short symbol for a length unit, e.g. ``"inches"`` → ``"in"``."""
    _length_factor(unit)  # validate
    return _LENGTH_SYMBOLS[unit.lower()]


def lengths_equal(a: float, b: float) -> bool:
    """Whether two lengths (m) are equal within the engine's geometric tolerance."""
    return math.isclose(a, b, rel_tol=LENGTH_REL_TOL, abs_tol=LENGTH_ABS_TOL)
