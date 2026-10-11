"""Per-browser-tab application state for the NiceGUI frontend.

Every browser tab gets its own :class:`AppState`, which owns

- the :class:`CoilDesign` being edited — the single source of truth for
  the inputs,
- the latest :class:`FullSystemOutput`, computed from the design by
  :func:`~pyteslacoil.engine.system.calculate_system` (which never
  modifies the design), and
- two kinds of listeners: *result* listeners refresh the displays after
  every recalculation; *design* listeners rebuild the input widgets after
  the design changes underneath them (preset load, unit change, an
  automatic adjustment).

Input widgets validate what the user typed, store it in ``state.design``
with :meth:`AppState.set_section` and so trigger a recalculation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from pyteslacoil.engine.system import calculate_system
from pyteslacoil.models import CoilDesign, FullSystemOutput, UnitSystem

logger = logging.getLogger(__name__)

# Listeners may return anything (e.g. NiceGUI's refresh response); it is ignored.
Listener = Callable[["AppState"], object]


class AppState:
    def __init__(self, design: CoilDesign | None = None) -> None:
        self.design: CoilDesign = design if design is not None else CoilDesign()
        self.outputs: FullSystemOutput = FullSystemOutput()
        self.error: str | None = None
        self._result_listeners: list[Listener] = []
        self._design_listeners: list[Listener] = []

    # ------------------------------------------------------------------
    # listener plumbing
    # ------------------------------------------------------------------
    def subscribe(self, callback: Listener) -> None:
        """Call ``callback(state)`` after every recalculation."""
        self._result_listeners.append(callback)

    def on_design_replaced(self, callback: Listener) -> None:
        """Call ``callback(state)`` when input widgets must be rebuilt from the design."""
        self._design_listeners.append(callback)

    def _emit(self, listeners: list[Listener]) -> None:
        for callback in list(listeners):
            try:
                callback(self)
            except Exception:  # a broken display must not break the others
                logger.exception("UI listener %r failed", callback)

    # ------------------------------------------------------------------
    # design changes
    # ------------------------------------------------------------------
    def set_section(self, name: str, value: Any) -> None:
        """Store a (validated) design section the user just edited and recalculate."""
        setattr(self.design, name, value)
        self.recalculate()

    def apply_section(self, name: str, value: Any) -> None:
        """Change a design section programmatically: rebuild the inputs and recalculate."""
        setattr(self.design, name, value)
        self._emit(self._design_listeners)
        self.recalculate()

    def replace_design(self, design: CoilDesign) -> None:
        """Replace the whole design (e.g. a preset): rebuild the inputs and recalculate."""
        self.design = design
        self._emit(self._design_listeners)
        self.recalculate()

    def set_unit_system(self, unit_system: UnitSystem) -> None:
        """Switch the display unit system; values are stored in SI and do not change."""
        if unit_system == self.design.unit_system:
            return
        self.design.unit_system = unit_system
        self._emit(self._design_listeners)
        self.recalculate()

    # ------------------------------------------------------------------
    # main recompute
    # ------------------------------------------------------------------
    def recalculate(self) -> None:
        """Recompute every output from the design and notify the result listeners."""
        try:
            self.outputs = calculate_system(self.design)
            self.error = None
        except Exception as exc:  # keep the UI usable and show what went wrong
            logger.exception("Calculation failed")
            self.outputs = FullSystemOutput()
            self.error = f"Calculation failed: {exc}"
        self._emit(self._result_listeners)
