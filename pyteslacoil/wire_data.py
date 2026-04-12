"""AWG wire gauge table.

Standard Phelps-Dodge / NEC wire data for round magnet wire. Used by the
secondary and primary modules to look up bare wire diameter and DC
resistance per unit length.

Each entry contains:

- ``bare_diameter_in``  — bare conductor diameter, inches
- ``bare_diameter_mm``  — bare conductor diameter, millimeters
- ``bare_diameter_m``   — bare conductor diameter, meters (SI cache)
- ``resistance_per_ft`` — DC resistance at 20 °C, ohms/foot
- ``resistance_per_m``  — DC resistance at 20 °C, ohms/meter
- ``insulated_diameter_in`` — typical single-build enamel diameter, inches
"""

from __future__ import annotations

# Note: insulated_diameter_in is approximate, single-build enamel.
AWG_TABLE: dict[int, dict[str, float]] = {
    4:  {"bare_diameter_in": 0.2043, "bare_diameter_mm": 5.189, "resistance_per_ft": 0.000253, "resistance_per_m": 0.000831, "insulated_diameter_in": 0.2103},
    6:  {"bare_diameter_in": 0.1620, "bare_diameter_mm": 4.115, "resistance_per_ft": 0.000403, "resistance_per_m": 0.001322, "insulated_diameter_in": 0.1670},
    8:  {"bare_diameter_in": 0.1285, "bare_diameter_mm": 3.264, "resistance_per_ft": 0.000641, "resistance_per_m": 0.002103, "insulated_diameter_in": 0.1325},
    10: {"bare_diameter_in": 0.1019, "bare_diameter_mm": 2.588, "resistance_per_ft": 0.001018, "resistance_per_m": 0.003340, "insulated_diameter_in": 0.1054},
    12: {"bare_diameter_in": 0.0808, "bare_diameter_mm": 2.052, "resistance_per_ft": 0.001619, "resistance_per_m": 0.005314, "insulated_diameter_in": 0.0837},
    14: {"bare_diameter_in": 0.0641, "bare_diameter_mm": 1.628, "resistance_per_ft": 0.002575, "resistance_per_m": 0.008447, "insulated_diameter_in": 0.0666},
    16: {"bare_diameter_in": 0.0508, "bare_diameter_mm": 1.291, "resistance_per_ft": 0.004094, "resistance_per_m": 0.013428, "insulated_diameter_in": 0.0529},
    18: {"bare_diameter_in": 0.0403, "bare_diameter_mm": 1.024, "resistance_per_ft": 0.006510, "resistance_per_m": 0.021356, "insulated_diameter_in": 0.0422},
    20: {"bare_diameter_in": 0.0320, "bare_diameter_mm": 0.812, "resistance_per_ft": 0.010350, "resistance_per_m": 0.033948, "insulated_diameter_in": 0.0337},
    22: {"bare_diameter_in": 0.0253, "bare_diameter_mm": 0.644, "resistance_per_ft": 0.016460, "resistance_per_m": 0.054000, "insulated_diameter_in": 0.0268},
    24: {"bare_diameter_in": 0.0201, "bare_diameter_mm": 0.511, "resistance_per_ft": 0.026170, "resistance_per_m": 0.085840, "insulated_diameter_in": 0.0214},
    26: {"bare_diameter_in": 0.0159, "bare_diameter_mm": 0.405, "resistance_per_ft": 0.041620, "resistance_per_m": 0.136560, "insulated_diameter_in": 0.0171},
    28: {"bare_diameter_in": 0.0126, "bare_diameter_mm": 0.321, "resistance_per_ft": 0.066170, "resistance_per_m": 0.217100, "insulated_diameter_in": 0.0137},
    30: {"bare_diameter_in": 0.0100, "bare_diameter_mm": 0.255, "resistance_per_ft": 0.105200, "resistance_per_m": 0.345100, "insulated_diameter_in": 0.0111},
    32: {"bare_diameter_in": 0.0080, "bare_diameter_mm": 0.202, "resistance_per_ft": 0.167200, "resistance_per_m": 0.548600, "insulated_diameter_in": 0.0090},
    34: {"bare_diameter_in": 0.0063, "bare_diameter_mm": 0.160, "resistance_per_ft": 0.265800, "resistance_per_m": 0.872000, "insulated_diameter_in": 0.0072},
    36: {"bare_diameter_in": 0.0050, "bare_diameter_mm": 0.127, "resistance_per_ft": 0.422600, "resistance_per_m": 1.386400, "insulated_diameter_in": 0.0058},
    38: {"bare_diameter_in": 0.0040, "bare_diameter_mm": 0.101, "resistance_per_ft": 0.671600, "resistance_per_m": 2.203000, "insulated_diameter_in": 0.0047},
    40: {"bare_diameter_in": 0.0031, "bare_diameter_mm": 0.080, "resistance_per_ft": 1.069000, "resistance_per_m": 3.506000, "insulated_diameter_in": 0.0038},
    42: {"bare_diameter_in": 0.0025, "bare_diameter_mm": 0.064, "resistance_per_ft": 1.700000, "resistance_per_m": 5.577000, "insulated_diameter_in": 0.0030},
    44: {"bare_diameter_in": 0.0020, "bare_diameter_mm": 0.051, "resistance_per_ft": 2.593000, "resistance_per_m": 8.507000, "insulated_diameter_in": 0.0024},
}

# Pre-cache an SI-meters version of the bare diameter so callers don't have
# to convert every lookup.
for _gauge, _row in AWG_TABLE.items():
    _row["bare_diameter_m"] = _row["bare_diameter_in"] * 0.0254
    _row["insulated_diameter_m"] = _row["insulated_diameter_in"] * 0.0254


AVAILABLE_AWG: list[int] = sorted(AWG_TABLE.keys())


def get_wire(awg: int) -> dict[str, float]:
    """Return the wire data row for the given AWG gauge.

    Raises
    ------
    KeyError
        If the gauge is not present in :data:`AWG_TABLE`.
    """
    if awg not in AWG_TABLE:
        raise KeyError(
            f"AWG {awg} not in wire table. Available: {AVAILABLE_AWG}"
        )
    return AWG_TABLE[awg]


def bare_diameter_m(awg: int) -> float:
    """Return the bare conductor diameter in meters for the given AWG."""
    return get_wire(awg)["bare_diameter_m"]


def resistance_per_meter(awg: int) -> float:
    """Return the DC resistance per meter (Ω/m) at 20 °C for the given AWG."""
    return get_wire(awg)["resistance_per_m"]
