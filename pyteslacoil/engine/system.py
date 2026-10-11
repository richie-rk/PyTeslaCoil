"""System-level calculation: every module of a :class:`CoilDesign` combined.

:func:`calculate_system` is a pure function — it never modifies the design.
It ties the modules together the way a builder would:

- the topload capacitance is corrected for the environment and loads the
  secondary, giving the system resonant frequency;
- with ``auto_tune`` the primary is tapped at the turn count matching that
  frequency (reported as ``tuned_primary``) and coupling uses that geometry;
- the spark gaps take their charging voltage, tank capacitance and line
  frequency from the transformer and primary, so each value has a single
  source of truth;
- the selected spark gap (``spark_gap_type``) drives the spark-length and
  terminal-voltage estimates;
- implausible or failed results are reported in ``warnings`` instead of
  being silently replaced.
"""

from __future__ import annotations

import math
from typing import TypeVar

import numpy as np

from pyteslacoil.engine.coupling import calculate_coupling
from pyteslacoil.engine.environment import calculate_environment
from pyteslacoil.engine.primary import calculate_primary
from pyteslacoil.engine.resonance import resonant_frequency
from pyteslacoil.engine.secondary import calculate_secondary
from pyteslacoil.engine.spark_gap_rotary import calculate_rotary_gap
from pyteslacoil.engine.spark_gap_static import calculate_static_gap
from pyteslacoil.engine.spark_length import (
    spark_length_from_energy,
    spark_length_from_power,
    terminal_voltage_estimate,
)
from pyteslacoil.engine.topload import calculate_topload
from pyteslacoil.engine.transformer import calculate_transformer
from pyteslacoil.engine.tuning import AutoTuneError, auto_tune_primary, tuning_ratio
from pyteslacoil.models import (
    CoilDesign,
    CouplingInput,
    FullSystemOutput,
    PrimaryInput,
    RotaryGapInput,
    SecondaryInput,
    SecondaryOutput,
    SparkGapType,
    StaticGapInput,
    TransformerOutput,
)
from pyteslacoil.units import length_in, length_symbol
from pyteslacoil.wire_data import bare_diameter_m, insulated_diameter_m

WINDING_FIT_TOLERANCE: float = 0.97
"""The wire table lists heavy-build enamel; single-build wire is ~3 % thinner."""

_GapInput = TypeVar("_GapInput", StaticGapInput, RotaryGapInput)


def resolve_spark_gap_type(design: CoilDesign) -> SparkGapType:
    """The gap that drives the coil: the explicit choice, else the configured gap."""
    if design.spark_gap_type is not None:
        return design.spark_gap_type
    if design.static_gap is not None:
        return SparkGapType.STATIC
    if design.rotary_gap is not None:
        return SparkGapType.ROTARY
    return SparkGapType.NONE


def _fmt_length(value_m: float, unit: str) -> str:
    """Length in the design's unit with four significant figures, e.g. ``10.03 in``."""
    value = length_in(value_m, unit)
    decimals = 3 - math.floor(math.log10(abs(value))) if value else 0
    return f"{value:.{max(0, decimals)}f} {length_symbol(unit)}"


def _secondary_warnings(sec: SecondaryInput, out: SecondaryOutput, unit: str) -> list[str]:
    pitch = out.wire_spacing_m
    bare = bare_diameter_m(sec.wire_awg)
    insulated = insulated_diameter_m(sec.wire_awg)
    if pitch < bare:
        return [
            f"Secondary turns overlap: {sec.turns} turns of AWG {sec.wire_awg} need at least "
            f"{_fmt_length(sec.turns * bare, unit)} of winding length, but the winding is "
            f"{_fmt_length(out.winding_height_m, unit)} long."
        ]
    if pitch < WINDING_FIT_TOLERANCE * insulated:
        return [
            f"Secondary winding does not fit: the turn pitch ({_fmt_length(pitch, unit)}) is "
            f"smaller than insulated AWG {sec.wire_awg} wire ({_fmt_length(insulated, unit)}). "
            "Use thinner wire, fewer turns or a longer winding."
        ]
    return []


def _primary_warnings(pri: PrimaryInput, sec: SecondaryInput | None, unit: str) -> list[str]:
    warnings: list[str] = []
    spacing = math.hypot(pri.radius_2 - pri.radius_1, pri.height_2 - pri.height_1) / pri.turns
    if spacing < pri.wire_diameter:
        warnings.append(
            f"Primary turns overlap: the turn spacing ({_fmt_length(spacing, unit)}) is smaller "
            f"than the conductor diameter ({_fmt_length(pri.wire_diameter, unit)})."
        )
    if sec is not None:
        t = np.linspace(0.0, 1.0, 101)
        r_pri = pri.radius_1 + (pri.radius_2 - pri.radius_1) * t
        h_pri = pri.height_1 + (pri.height_2 - pri.height_1) * t
        inside = (h_pri >= sec.height_1) & (h_pri <= sec.height_2)
        frac = (h_pri - sec.height_1) / (sec.height_2 - sec.height_1)
        r_sec = sec.radius_1 + (sec.radius_2 - sec.radius_1) * frac
        if np.any(inside & (r_pri <= r_sec)):
            warnings.append("The primary winding intersects the secondary winding.")
    return warnings


# Gap fields that describe the tank circuit:
# (field, design source, display scale, display unit, how to provide it if missing).
_TANK_FIELDS: tuple[tuple[str, str, float, str, str | None], ...] = (
    ("transformer_voltage_peak", "transformer peak voltage", 1e-3, "kV",
     "configure a transformer or set the gap's transformer_voltage_peak"),
    ("tank_capacitance", "primary tank capacitance", 1e9, "nF",
     "configure a primary or set the gap's tank_capacitance"),
    ("line_frequency_hz", "transformer line frequency", 1.0, "Hz", None),
)  # fmt: skip


def _design_tank_values(
    design: CoilDesign, xfmr: TransformerOutput | None
) -> dict[str, float | None]:
    return {
        "transformer_voltage_peak": xfmr.output_voltage_peak if xfmr else None,
        "tank_capacitance": design.primary.capacitance if design.primary else None,
        "line_frequency_hz": design.transformer.line_frequency_hz if design.transformer else None,
    }


def _with_tank_parameters(
    gap: _GapInput, label: str, design_values: dict[str, float | None], warnings: list[str]
) -> _GapInput | None:
    """Fill in the gap's charging voltage, tank capacitance and line frequency.

    Values from the transformer and primary win (single source of truth);
    a conflicting value on the gap itself is reported. Returns ``None`` when
    a required value is available from neither.
    """
    data = gap.model_dump()
    for field, source, scale, symbol, hint in _TANK_FIELDS:
        own, design_value = data[field], design_values[field]
        if design_value is None:
            if own is None and hint is not None:
                warnings.append(f"{label} not calculated: {hint}.")
                return None
            continue
        if own is not None and not math.isclose(own, design_value, rel_tol=1e-3):
            warnings.append(
                f"{label}: its {field} ({own * scale:.4g} {symbol}) differs from the {source} "
                f"({design_value * scale:.4g} {symbol}); the {source} is used."
            )
        data[field] = design_value
    return type(gap).model_validate(data)


def calculate_system(design: CoilDesign) -> FullSystemOutput:
    """Compute every configured module of ``design`` and the system results."""
    warnings: list[str] = []
    unit = design.unit_system.value

    sec_out = calculate_secondary(design.secondary) if design.secondary else None
    top_out = calculate_topload(design.topload) if design.topload else None

    # ── Environment-corrected topload and the loaded secondary resonance ──
    env_out = None
    if design.environment is not None:
        env_out = calculate_environment(
            design.environment,
            topload_height_m=design.topload.height if design.topload else None,
            topload_capacitance_f=top_out.capacitance_f if top_out else None,
        )
        warnings.extend(env_out.warnings)

    c_top = None
    if top_out is not None and top_out.capacitance_f > 0:
        c_top = top_out.capacitance_f * (env_out.proximity_correction_factor if env_out else 1.0)

    f_sys = c_terminal = None
    if design.secondary is not None and sec_out is not None:
        c_terminal = sec_out.self_capacitance_f + (c_top or 0.0)
        f_sys = resonant_frequency(sec_out.inductance_h, c_terminal)
        if c_top:
            sec_out = sec_out.model_copy(
                update={"system_capacitance_f": c_terminal, "system_resonant_frequency_hz": f_sys}
            )
        warnings.extend(_secondary_warnings(design.secondary, sec_out, unit))
        top = design.topload
        if top is not None and top.height is not None and top.height < design.secondary.height_2:
            warnings.append("The topload centre is below the top of the secondary winding.")

    # ── Primary, optionally tapped by auto-tune ──
    pri_out = tuned = None
    effective_primary = design.primary
    if design.primary is not None:
        if design.auto_tune and f_sys is not None:
            try:
                tuned, pri_out = auto_tune_primary(f_sys, design.primary)
            except AutoTuneError as exc:
                warnings.append(f"Auto-tune failed: {exc}.")
        if pri_out is None:
            pri_out = calculate_primary(design.primary)
            if f_sys is not None:
                ratio = tuning_ratio(f_sys, pri_out.resonant_frequency_hz)
                pri_out = pri_out.model_copy(update={"tuning_ratio": ratio})
        effective_primary = tuned if tuned is not None else design.primary
        warnings.extend(_primary_warnings(effective_primary, design.secondary, unit))

    cpl_out = None
    if effective_primary is not None and design.secondary is not None:
        cpl_out = calculate_coupling(
            CouplingInput(primary=effective_primary, secondary=design.secondary),
            operating_frequency_hz=f_sys,
        )
        if cpl_out.coupling_coefficient >= 1.0:
            warnings.append(
                f"The coupling coefficient k = {cpl_out.coupling_coefficient:.3f} is unphysical "
                "(k must be below 1); check that the coils do not overlap."
            )

    # ── Transformer and spark gaps ──
    xfmr_out = calculate_transformer(design.transformer) if design.transformer else None

    tank_values = _design_tank_values(design, xfmr_out)
    static_out = rotary_out = None
    if design.static_gap is not None:
        static_in = _with_tank_parameters(design.static_gap, "Static gap", tank_values, warnings)
        static_out = calculate_static_gap(static_in) if static_in else None
    if design.rotary_gap is not None:
        rotary_in = _with_tank_parameters(design.rotary_gap, "Rotary gap", tank_values, warnings)
        rotary_out = calculate_rotary_gap(rotary_in) if rotary_in else None

    active = resolve_spark_gap_type(design)
    bps = energy = 0.0
    spark: float | None = None
    if active == SparkGapType.STATIC:
        if design.static_gap is None:
            warnings.append("The static spark gap is selected but not configured.")
        elif static_out is not None:
            if static_out.fires:
                bps, energy = static_out.bps, static_out.effective_cap_energy_j
            else:
                spark = 0.0
                warnings.append(
                    f"The static gap never fires: its breakdown voltage "
                    f"({static_out.breakdown_voltage_v / 1e3:.1f} kV) exceeds the peak charging "
                    "voltage. Reduce the gap spacing."
                )
    elif active == SparkGapType.ROTARY:
        if design.rotary_gap is None:
            warnings.append("The rotary spark gap is selected but not configured.")
        elif rotary_out is not None:
            bps, energy = rotary_out.bps, rotary_out.effective_cap_energy_j

    if bps > 0 and energy > 0:
        spark = spark_length_from_energy(bps, energy)
    elif spark is None and xfmr_out is not None:
        spark = spark_length_from_power(xfmr_out.input_power_w)

    v_term = None
    if c_terminal:
        if energy > 0:
            v_term = terminal_voltage_estimate(energy, c_terminal)
        # Report the gaps' terminal voltage with the design's real capacitance.
        if static_out is not None:
            v = terminal_voltage_estimate(static_out.effective_cap_energy_j, c_terminal)
            static_out = static_out.model_copy(update={"terminal_voltage_v": v})
        if rotary_out is not None:
            v = terminal_voltage_estimate(rotary_out.effective_cap_energy_j, c_terminal)
            rotary_out = rotary_out.model_copy(update={"terminal_voltage_v": v})

    return FullSystemOutput(
        secondary=sec_out,
        primary=pri_out,
        topload=top_out,
        coupling=cpl_out,
        static_gap=static_out,
        rotary_gap=rotary_out,
        transformer=xfmr_out,
        environment=env_out,
        tuned_primary=tuned,
        active_spark_gap=active,
        effective_topload_capacitance_f=c_top,
        system_resonant_frequency_hz=f_sys,
        tuning_ratio=pri_out.tuning_ratio if pri_out else None,
        estimated_spark_length_m=spark,
        estimated_terminal_voltage_v=v_term,
        warnings=warnings,
    )
