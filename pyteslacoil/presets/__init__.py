"""Demo coil preset registry.

Each preset is a function that returns a fully-populated
:class:`CoilDesign`. The :func:`load_preset` helper looks up by ID and is
used by the UI's preset dialog.
"""

from typing import Callable

from pyteslacoil.models.coil_design import CoilDesign
from pyteslacoil.presets.demo_drsstc import build as _drsstc
from pyteslacoil.presets.demo_medium_sgtc import build as _medium
from pyteslacoil.presets.demo_small_sgtc import build as _small

AVAILABLE_PRESETS: dict[str, str] = {
    "small_sgtc": "Small SGTC (Hackaday Mini)",
    "medium_sgtc": "Medium SGTC (TCML reference)",
    "drsstc": "DRSSTC (compact)",
}

_BUILDERS: dict[str, Callable[[], CoilDesign]] = {
    "small_sgtc": _small,
    "medium_sgtc": _medium,
    "drsstc": _drsstc,
}


def load_preset(preset_id: str) -> CoilDesign:
    if preset_id not in _BUILDERS:
        raise KeyError(f"Unknown preset: {preset_id}")
    return _BUILDERS[preset_id]()
