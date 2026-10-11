"""AWG wire gauge table.

Round copper magnet wire data used by the secondary and primary modules to
look up conductor diameter and DC resistance per unit length.

Each entry is a read-only mapping containing:

- ``bare_diameter_in`` / ``bare_diameter_mm`` / ``bare_diameter_m`` — bare
  conductor diameter from the AWG definition (ASTM B258):
  ``d = 0.005 in · 92^((36 − n) / 39)``
- ``resistance_per_m`` / ``resistance_per_ft`` — DC resistance at 20 °C,
  derived from the bare diameter and the IACS resistivity of annealed
  copper (:data:`pyteslacoil.constants.COPPER_RESISTIVITY`)
- ``insulated_diameter_in`` / ``insulated_diameter_m`` — typical overall
  diameter of heavy-build enamel wire (single-build wire is ~3 % thinner)
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from pyteslacoil.constants import COPPER_RESISTIVITY, FT_TO_M, INCH_TO_M, PI

# Typical heavy-build enamel overall diameter (inches).
_INSULATED_DIAMETER_IN: dict[int, float] = {
    4: 0.2103,
    6: 0.1670,
    8: 0.1325,
    10: 0.1054,
    12: 0.0837,
    14: 0.0666,
    16: 0.0529,
    18: 0.0422,
    20: 0.0337,
    22: 0.0268,
    24: 0.0214,
    26: 0.0171,
    28: 0.0137,
    30: 0.0111,
    32: 0.0090,
    34: 0.0072,
    36: 0.0058,
    38: 0.0047,
    40: 0.0038,
    42: 0.0030,
    44: 0.0024,
}


def _bare_diameter_in(awg: int) -> float:
    return 0.005 * 92.0 ** ((36 - awg) / 39.0)


def _row(awg: int, insulated_in: float) -> Mapping[str, float]:
    d_in = _bare_diameter_in(awg)
    d_m = d_in * INCH_TO_M
    r_per_m = COPPER_RESISTIVITY / (PI * (0.5 * d_m) ** 2)
    return MappingProxyType(
        {
            "bare_diameter_in": d_in,
            "bare_diameter_mm": d_m * 1e3,
            "bare_diameter_m": d_m,
            "resistance_per_m": r_per_m,
            "resistance_per_ft": r_per_m * FT_TO_M,
            "insulated_diameter_in": insulated_in,
            "insulated_diameter_m": insulated_in * INCH_TO_M,
        }
    )


AWG_TABLE: Mapping[int, Mapping[str, float]] = MappingProxyType(
    {awg: _row(awg, ins) for awg, ins in sorted(_INSULATED_DIAMETER_IN.items())}
)

AVAILABLE_AWG: list[int] = sorted(AWG_TABLE.keys())


def get_wire(awg: int) -> Mapping[str, float]:
    """Return the wire data row for the given AWG gauge.

    Raises
    ------
    KeyError
        If the gauge is not present in :data:`AWG_TABLE`.
    """
    if awg not in AWG_TABLE:
        raise KeyError(f"AWG {awg} not in wire table. Available: {AVAILABLE_AWG}")
    return AWG_TABLE[awg]


def bare_diameter_m(awg: int) -> float:
    """Return the bare conductor diameter in meters for the given AWG."""
    return get_wire(awg)["bare_diameter_m"]


def insulated_diameter_m(awg: int) -> float:
    """Return the typical insulated (heavy-build enamel) diameter in meters."""
    return get_wire(awg)["insulated_diameter_m"]


def resistance_per_meter(awg: int) -> float:
    """Return the DC resistance per meter (Ω/m) at 20 °C for the given AWG."""
    return get_wire(awg)["resistance_per_m"]
