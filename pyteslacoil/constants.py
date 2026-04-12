"""Physical constants used throughout the calculations.

All values are SI unless explicitly noted. The calculator works in SI
internally and only converts at user input/output boundaries.
"""

import math

# ---------------------------------------------------------------------------
# Electromagnetic constants
# ---------------------------------------------------------------------------
MU_0: float = 4.0 * math.pi * 1e-7
"""Permeability of free space (H/m)."""

EPSILON_0: float = 8.854_187_817e-12
"""Permittivity of free space (F/m)."""

C_LIGHT: float = 299_792_458.0
"""Speed of light in vacuum (m/s)."""

PI: float = math.pi

# ---------------------------------------------------------------------------
# Air breakdown — used for spark gap and topload breakout estimation
# ---------------------------------------------------------------------------
AIR_BREAKDOWN_V_PER_M: float = 3.0e6
"""Approximate dielectric strength of dry air at STP (V/m). ~30 kV/cm."""

AIR_BREAKDOWN_V_PER_INCH: float = 75_000.0
"""Approximate field strength to break down a 1-inch air gap at STP (V)."""

# ---------------------------------------------------------------------------
# Copper properties (used for wire resistance and skin depth)
# ---------------------------------------------------------------------------
COPPER_RESISTIVITY: float = 1.68e-8
"""Resistivity of copper at 20 °C (Ω·m)."""

COPPER_TEMP_COEFF: float = 0.003_93
"""Temperature coefficient of copper resistance (per °C)."""

COPPER_PERMEABILITY: float = 1.0
"""Relative permeability of copper (essentially non-magnetic)."""

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_TEMP_F: float = 68.0
DEFAULT_TEMP_C: float = 20.0
DEFAULT_LINE_FREQUENCY_HZ: float = 60.0

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------
INCH_TO_M: float = 0.0254
M_TO_INCH: float = 1.0 / 0.0254
FT_TO_M: float = 0.3048
M_TO_FT: float = 1.0 / 0.3048
