"""PyTeslaCoil — open-source Tesla coil design calculator.

Pure-Python physics engine + Pydantic models. The :mod:`pyteslacoil.ui`
subpackage contains the NiceGUI frontend; the engine never imports it and
may be used as a standalone library.
"""

from pyteslacoil.engine.coupling import calculate_coupling
from pyteslacoil.engine.environment import calculate_environment
from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.engine.spark_gap_rotary import calculate_rotary_gap
from pyteslacoil.engine.spark_gap_static import calculate_static_gap
from pyteslacoil.engine.spark_length import estimate_spark_length
from pyteslacoil.engine.system import calculate_system
from pyteslacoil.engine.topload import calculate_topload
from pyteslacoil.engine.transformer import calculate_transformer
from pyteslacoil.engine.tuning import AutoTuneError, auto_tune

__all__ = [
    "calculate_system",
    "calculate_secondary",
    "calculate_primary",
    "calculate_topload",
    "calculate_coupling",
    "calculate_static_gap",
    "calculate_rotary_gap",
    "calculate_transformer",
    "calculate_environment",
    "estimate_spark_length",
    "auto_tune",
    "AutoTuneError",
]

__version__ = "1.0.0"
