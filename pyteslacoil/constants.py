"""Physical constants and defaults used throughout the calculations.

All values are SI unless explicitly noted. The calculator works in SI
internally and only converts at user input/output boundaries.
"""

import math

from scipy import constants as _codata

# ---------------------------------------------------------------------------
# Electromagnetic constants (CODATA values as shipped with SciPy)
# ---------------------------------------------------------------------------
MU_0: float = float(_codata.mu_0)
"""Permeability of free space (H/m)."""

EPSILON_0: float = float(_codata.epsilon_0)
"""Permittivity of free space (F/m)."""

C_LIGHT: float = float(_codata.c)
"""Speed of light in vacuum (m/s)."""

PI: float = math.pi

# ---------------------------------------------------------------------------
# Copper properties (used for wire resistance and skin depth)
# ---------------------------------------------------------------------------
COPPER_RESISTIVITY: float = 1.7241e-8
"""Resistivity of annealed copper (IACS, the magnet-wire standard) at
:data:`COPPER_REFERENCE_TEMP_C` (Ω·m)."""

COPPER_REFERENCE_TEMP_C: float = 20.0
"""Temperature at which :data:`COPPER_RESISTIVITY` and the wire table apply (°C)."""

COPPER_TEMP_COEFF: float = 0.003_93
"""Temperature coefficient of copper resistance (per °C)."""

COPPER_PERMEABILITY: float = 1.0
"""Relative permeability of copper (essentially non-magnetic)."""

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_TEMP_C: float = 20.0
DEFAULT_LINE_FREQUENCY_HZ: float = 60.0

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------
INCH_TO_M: float = 0.0254
M_TO_INCH: float = 1.0 / INCH_TO_M
FT_TO_M: float = 0.3048
M_TO_FT: float = 1.0 / FT_TO_M

# ---------------------------------------------------------------------------
# Numerical tolerances
# ---------------------------------------------------------------------------
LENGTH_REL_TOL: float = 1e-6
"""Relative tolerance used when deciding whether two lengths are equal."""

LENGTH_ABS_TOL: float = 1e-9
"""Absolute tolerance (m) used when deciding whether two lengths are equal."""
