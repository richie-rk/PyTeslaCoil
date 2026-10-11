"""Results tab: headline metrics, warnings, exports and the coil cross-section."""

from __future__ import annotations

import logging

from nicegui import ui

from pyteslacoil.export.consolidated import to_text
from pyteslacoil.export.json_export import to_json
from pyteslacoil.export.pdf_export import to_pdf_bytes
from pyteslacoil.models import RotaryGapOutput, SparkGapType, StaticGapOutput
from pyteslacoil.ui.components.cards import (
    DASH,
    clear_rows,
    coupling_quality,
    fmt,
    metric_card,
    result_rows,
    results_grid,
    section_card,
)
from pyteslacoil.ui.components.coil_visualizer import build as build_visualizer
from pyteslacoil.ui.components.inputs import trusted_html
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import (
    ACCENT,
    ACCENT_INFO,
    ACCENT_WARN,
    BAD,
    OUTLINE_BUTTON_STYLE,
    PRIMARY_BUTTON_STYLE,
    SURFACE,
    SURFACE_BORDER,
    TEXT,
    WARN,
)
from pyteslacoil.units import length_in, length_symbol

logger = logging.getLogger(__name__)


def _export_card(state: AppState) -> None:
    with ui.card().classes("w-full").style(
        f"background: {SURFACE}; border: 1px solid {SURFACE_BORDER}; "
        f"border-radius: 8px; padding: 16px;"
    ):
        ui.label("Export").classes("text-sm font-semibold mb-2").style(f"color: {TEXT};")
        text_area = (
            ui.textarea(label="Output", value="Click an export button to populate.")
            .classes("w-full font-mono text-xs")
            .props("autogrow rows=12 readonly")
        )

        def do_text() -> None:
            text_area.value = to_text(state.design, state.outputs)

        def do_json() -> None:
            text_area.value = to_json(state.design, state.outputs)

        def do_pdf() -> None:
            try:
                pdf_bytes = to_pdf_bytes(state.design, state.outputs)
            except Exception as exc:  # report any rendering failure to the user
                logger.exception("PDF export failed")
                ui.notify(f"PDF export failed: {exc}", type="warning")
                return
            ui.download.content(pdf_bytes, "pyteslacoil_export.pdf", "application/pdf")

        with ui.row().classes("gap-3 mt-3 flex-wrap"):
            ui.button("Export Text", icon="description", on_click=do_text).style(PRIMARY_BUTTON_STYLE)
            ui.button("Export JSON", icon="data_object", on_click=do_json).style(OUTLINE_BUTTON_STYLE)
            ui.button("Export PDF", icon="picture_as_pdf", on_click=do_pdf).style(OUTLINE_BUTTON_STYLE)


def render(state: AppState) -> None:
    # ── Headline metric cards ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 flex-wrap"):
        freq_val, _ = metric_card("Resonant Frequency", DASH, "kHz", ACCENT)
        k_val, _ = metric_card("Coupling Coefficient", DASH, "", ACCENT_WARN)
        spark_val, spark_unit = metric_card("Estimated Spark Length", DASH, "", ACCENT_INFO)

    error_label = ui.label().classes("w-full mt-4 text-sm").style(f"color: {BAD};")
    error_label.set_visibility(False)

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap mt-4"):
        # ── Detailed results ───────────────────────────────────────
        with ui.column().classes("flex-[6] sm:min-w-[300px] gap-4"):
            with section_card("Warnings", "warning") as warnings_card:
                warnings_column = ui.column().classes("gap-1")

            with section_card("Secondary Results", "bolt"):
                sec_rows = result_rows(
                    results_grid(),
                    {
                        "L": "Inductance",
                        "C": "Self-capacitance",
                        "f": "Bare frequency",
                        "fsys": "System frequency",
                        "ctop": "Topload capacitance",
                    },
                )

            with section_card("Primary Results", "track_changes"):
                pri_rows = result_rows(
                    results_grid(),
                    {
                        "L": "Total inductance",
                        "f": "Resonant frequency",
                        "tune": "Tuning ratio",
                        "turns": "Turns in use",
                    },
                )

            with section_card("Coupling & Drive", "link"):
                drive_rows = result_rows(
                    results_grid(),
                    {
                        "k": "Coupling k",
                        "gap": "Spark gap",
                        "bps": "BPS",
                        "e": "Energy / bang",
                        "vterm": "Terminal voltage",
                    },
                )

            _export_card(state)

        # ── Visualizer ─────────────────────────────────────────────
        with ui.column().classes("flex-[4] sm:min-w-[300px]"):
            with section_card("Coil Cross-Section", "straighten"):
                svg_holder = trusted_html("").classes("w-full")

    # ── Reactive refresh ───────────────────────────────────────────
    def refresh(s: AppState) -> None:
        out = s.outputs
        unit = s.design.unit_system.value

        error_label.text = s.error or ""
        error_label.set_visibility(s.error is not None)

        warnings_card.set_visibility(bool(out.warnings))
        warnings_column.clear()
        with warnings_column:
            for warning in out.warnings:
                ui.label(f"⚠ {warning}").classes("text-sm").style(f"color: {WARN};")

        freq_val.text = fmt(out.system_resonant_frequency_khz, ".2f")
        spark_unit.text = length_symbol(unit)
        spark = out.estimated_spark_length_m
        spark_val.text = DASH if spark is None else f"{length_in(spark, unit):.1f}"

        if out.secondary is None:
            clear_rows(sec_rows)
        else:
            sec_rows["L"].text = f"{out.secondary.inductance_mh:.3f} mH"
            sec_rows["C"].text = f"{out.secondary.self_capacitance_pf:.2f} pF"
            sec_rows["f"].text = f"{out.secondary.resonant_frequency_khz:.2f} kHz"
            sec_rows["fsys"].text = fmt(out.system_resonant_frequency_khz, ".2f", "kHz")
            sec_rows["ctop"].text = fmt(out.effective_topload_capacitance_pf, ".2f", "pF")

        if out.primary is None:
            clear_rows(pri_rows)
        else:
            pri_rows["L"].text = f"{out.primary.total_inductance_uh:.2f} µH"
            pri_rows["f"].text = f"{out.primary.resonant_frequency_khz:.2f} kHz"
            pri_rows["tune"].text = fmt(out.tuning_ratio, ".3f")
            primary = out.tuned_primary or s.design.primary
            pri_rows["turns"].text = fmt(primary.turns if primary else None, ".4f")
            if out.tuned_primary is not None:
                pri_rows["turns"].text += " (auto-tuned)"

        if out.coupling is None:
            k_val.text = DASH
            drive_rows["k"].text = DASH
        else:
            k = out.coupling.coupling_coefficient
            k_val.text = f"{k:.4f}"
            drive_rows["k"].text = f"{k:.4f}"
            drive_rows["k"].style(f"color: {coupling_quality(k)[1]} !important;")
        drive_rows["gap"].text = out.active_spark_gap.value if out.active_spark_gap else DASH
        gap_out: StaticGapOutput | RotaryGapOutput | None = None
        if out.active_spark_gap == SparkGapType.STATIC:
            gap_out = out.static_gap
        elif out.active_spark_gap == SparkGapType.ROTARY:
            gap_out = out.rotary_gap
        drive_rows["bps"].text = fmt(gap_out.bps if gap_out else None, ".0f")
        drive_rows["e"].text = fmt(gap_out.effective_cap_energy_j if gap_out else None, ".3f", "J")
        v_term = out.estimated_terminal_voltage_v
        drive_rows["vterm"].text = fmt(None if v_term is None else v_term / 1e3, ".0f", "kV")

        svg_holder.content = build_visualizer(s.design, out.tuned_primary)

    state.subscribe(refresh)
