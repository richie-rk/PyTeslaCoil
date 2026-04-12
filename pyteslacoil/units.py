"""Unit conversion utilities.

The engine works in SI (meters, henries, farads, hertz) internally. Convert
to user-facing units only at the input/output boundary.
"""

# ---------------------------------------------------------------------------
# Length
# ---------------------------------------------------------------------------
def inches_to_meters(val: float) -> float:
    return val * 0.0254


def meters_to_inches(val: float) -> float:
    return val / 0.0254


def cm_to_meters(val: float) -> float:
    return val * 0.01


def meters_to_cm(val: float) -> float:
    return val * 100.0


def feet_to_meters(val: float) -> float:
    return val * 0.3048


def meters_to_feet(val: float) -> float:
    return val / 0.3048


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
# Generic helper — pick the right unit string for a length depending on
# user preference.
# ---------------------------------------------------------------------------
def length_in(value_m: float, unit: str) -> float:
    """Convert a length in meters to the requested user unit."""
    unit = unit.lower()
    if unit == "inches":
        return meters_to_inches(value_m)
    if unit == "cm":
        return meters_to_cm(value_m)
    if unit == "mm":
        return meters_to_mm(value_m)
    if unit in ("m", "meters"):
        return value_m
    raise ValueError(f"Unknown length unit: {unit!r}")


def length_to_meters(value: float, unit: str) -> float:
    """Convert a user-supplied length to meters."""
    unit = unit.lower()
    if unit == "inches":
        return inches_to_meters(value)
    if unit == "cm":
        return cm_to_meters(value)
    if unit == "mm":
        return mm_to_meters(value)
    if unit in ("m", "meters"):
        return value
    raise ValueError(f"Unknown length unit: {unit!r}")
