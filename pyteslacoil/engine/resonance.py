"""LC resonance helpers shared by the engine modules."""

from __future__ import annotations

import math

from pyteslacoil.constants import PI
from pyteslacoil.engine._checks import require_positive


def resonant_frequency(inductance_h: float, capacitance_f: float) -> float:
    """Resonant frequency of an LC circuit,  f = 1 / (2π √(L C))."""
    require_positive(inductance_h=inductance_h, capacitance_f=capacitance_f)
    return 1.0 / (2.0 * PI * math.sqrt(inductance_h * capacitance_f))


def characteristic_impedance(inductance_h: float, capacitance_f: float) -> float:
    """Characteristic (surge) impedance of an LC circuit,  Z = √(L / C)."""
    require_positive(inductance_h=inductance_h, capacitance_f=capacitance_f)
    return math.sqrt(inductance_h / capacitance_f)


def inductance_for_frequency(frequency_hz: float, capacitance_f: float) -> float:
    """Inductance that resonates with ``capacitance_f`` at ``frequency_hz``,  L = 1 / (ω² C)."""
    require_positive(frequency_hz=frequency_hz, capacitance_f=capacitance_f)
    omega = 2.0 * PI * frequency_hz
    return 1.0 / (omega * omega * capacitance_f)
