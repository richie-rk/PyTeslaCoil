"""Reactive application state for the NiceGUI frontend.

The :class:`AppState` instance owns:

- the :class:`CoilDesign` Pydantic state object (one source of truth)
- a list of subscriber callbacks that fire whenever a recompute completes
- a debounced ``recalculate`` method that the input widgets call

The pattern is intentionally simple: every input widget binds to a field on
``state.design``, then calls ``state.recalculate()``. The state recomputes
all engine outputs and notifies subscribers, who refresh their displays.
"""

from __future__ import annotations

import threading
from typing import Callable, List, Optional

from pyteslacoil.engine.coupling import calculate_coupling
from pyteslacoil.engine.environment import calculate_environment
from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.engine.spark_gap_rotary import calculate_rotary_gap
from pyteslacoil.engine.spark_gap_static import calculate_static_gap
from pyteslacoil.engine.spark_length import estimate_spark_length
from pyteslacoil.engine.topload import calculate_topload
from pyteslacoil.engine.transformer import calculate_transformer
from pyteslacoil.engine.tuning import auto_tune_primary, tuning_ratio
from pyteslacoil.models import (
    CoilDesign,
    CouplingInput,
    FullSystemOutput,
)


class AppState:

    def __init__(self, design: Optional[CoilDesign] = None) -> None:
        self.design: CoilDesign = design or CoilDesign()
        self.outputs: FullSystemOutput = FullSystemOutput()
        self._subscribers: List[Callable[["AppState"], None]] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # subscriber plumbing
    # ------------------------------------------------------------------
    def subscribe(self, callback: Callable[["AppState"], None]) -> None:
        self._subscribers.append(callback)

    def _notify(self) -> None:
        for cb in self._subscribers:
            try:
                cb(self)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[PyTeslaCoil] subscriber error: {exc}")

    # ------------------------------------------------------------------
    # main recompute
    # ------------------------------------------------------------------
    def recalculate(self) -> None:
        with self._lock:
            out = FullSystemOutput()

            sec_out = None
            top_out = None
            pri_out = None

            if self.design.secondary is not None:
                sec_out = calculate_secondary(self.design.secondary)
                out.secondary = sec_out

            if self.design.topload is not None:
                top_out = calculate_topload(self.design.topload)
                out.topload = top_out

            # Annotate the secondary with the system frequency that includes
            # the topload, if both are present.
            if sec_out is not None and top_out is not None and top_out.capacitance_pf > 0:
                c_total_pf = sec_out.self_capacitance_pf + top_out.capacitance_pf
                c_total = c_total_pf * 1e-12
                from math import pi, sqrt

                f_sys = 1.0 / (2.0 * pi * sqrt(sec_out.inductance_h * c_total))
                out.system_resonant_frequency_hz = f_sys
                out.system_resonant_frequency_khz = f_sys / 1000.0
                out.secondary = sec_out.model_copy(
                    update={
                        "system_capacitance_pf": c_total_pf,
                        "system_resonant_frequency_khz": f_sys / 1000.0,
                    }
                )
            elif sec_out is not None:
                out.system_resonant_frequency_hz = sec_out.resonant_frequency_hz
                out.system_resonant_frequency_khz = sec_out.resonant_frequency_khz

            if self.design.primary is not None:
                primary = self.design.primary
                if self.design.auto_tune and out.system_resonant_frequency_hz:
                    primary, pri_out = auto_tune_primary(
                        out.system_resonant_frequency_hz, primary
                    )
                    self.design.primary = primary
                else:
                    pri_out = calculate_primary(primary)
                    if out.system_resonant_frequency_hz:
                        pri_out = pri_out.model_copy(
                            update={
                                "tuning_ratio": tuning_ratio(
                                    out.system_resonant_frequency_hz,
                                    pri_out.resonant_frequency_hz,
                                )
                            }
                        )
                out.primary = pri_out
                out.tuning_ratio = pri_out.tuning_ratio

            if self.design.primary is not None and self.design.secondary is not None:
                out.coupling = calculate_coupling(
                    CouplingInput(
                        primary=self.design.primary,
                        secondary=self.design.secondary,
                        desired_k=self.design.desired_coupling,
                        auto_adjust_height=False,
                    )
                )

            if self.design.transformer is not None:
                out.transformer = calculate_transformer(self.design.transformer)

            if self.design.static_gap is not None:
                out.static_gap = calculate_static_gap(self.design.static_gap)
            if self.design.rotary_gap is not None:
                out.rotary_gap = calculate_rotary_gap(self.design.rotary_gap)

            if self.design.environment is not None:
                out.environment = calculate_environment(self.design.environment)

            # Aggregate spark length: prefer the energy form from whichever
            # gap is configured, falling back to the input power.
            input_power = (
                out.transformer.input_power_w if out.transformer else 0.0
            )
            bps = energy = 0.0
            if out.rotary_gap:
                bps, energy = out.rotary_gap.bps, out.rotary_gap.effective_cap_energy_j
            elif out.static_gap:
                bps, energy = out.static_gap.bps, out.static_gap.effective_cap_energy_j
            spark_m = estimate_spark_length(input_power, bps, energy)
            if spark_m > 0:
                out.estimated_spark_length_m = spark_m
                out.estimated_spark_length_in = spark_m / 0.0254

            self.outputs = out

        self._notify()
