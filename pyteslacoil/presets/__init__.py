"""Demo coil preset registry.

Each preset is a function that returns a fully-populated
:class:`CoilDesign`. The :func:`load_preset` helper looks up by ID and is
used by the UI's preset dialog.
"""

from collections.abc import Callable
from typing import NamedTuple

from pyteslacoil.models.coil_design import CoilDesign
from pyteslacoil.presets.demo_drsstc import build as _drsstc
from pyteslacoil.presets.demo_medium_sgtc import build as _medium
from pyteslacoil.presets.demo_small_sgtc import build as _small


class Preset(NamedTuple):
    label: str
    build: Callable[[], CoilDesign]


PRESETS: dict[str, Preset] = {
    "small_sgtc": Preset("Small SGTC (Hackaday Mini)", _small),
    "medium_sgtc": Preset("Medium SGTC (TCML reference)", _medium),
    "drsstc": Preset("DRSSTC (compact)", _drsstc),
}

AVAILABLE_PRESETS: dict[str, str] = {preset_id: p.label for preset_id, p in PRESETS.items()}
"""Preset ID → display label."""


def load_preset(preset_id: str) -> CoilDesign:
    """Build a fresh copy of the preset with the given ID."""
    try:
        preset = PRESETS[preset_id]
    except KeyError:
        raise KeyError(f"Unknown preset: {preset_id!r}; available: {list(PRESETS)}") from None
    return preset.build()
