from __future__ import annotations

from nicegui import ui

from ui.components.cards import (
    metric_card,
    result_row,
    results_grid,
    section_card,
)
from ui.state import AppState
from ui.theme import (
    ACCENT,
    ACCENT_INFO,
    ACCENT_WARN,
    BAD,
    GOOD,
    SURFACE,
    SURFACE_BORDER,
    TEXT,
    WARN,
)


def _quality(k: float) -> str:
    if 0.10 <= k <= 0.25:
        return GOOD
    if 0.05 <= k < 0.10 or 0.25 < k <= 0.30:
        return WARN
    return BAD


def render(state: AppState) -> None:
    from ui.components.coil_visualizer import build as build_visualizer

    # ── Headline metric cards ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 flex-wrap"):
        freq_val, freq_unit = metric_card(
            "Resonant Frequency", "\u2014", "kHz", ACCENT
        )
        k_val, k_unit = metric_card(
            "Coupling Coefficient", "\u2014", "", ACCENT_WARN
        )
        spark_val, spark_unit = metric_card(
            "Estimated Spark Length", "\u2014", "inches", ACCENT_INFO
        )

    with ui.row().classes("w-full gap-4 flex-wrap md:flex-nowrap mt-4"):
        # ── Detailed results ───────────────────────────────────────
        with ui.column().classes("flex-[6] min-w-[300px] gap-4"):
            # Secondary section
            with section_card("Secondary Results", "bolt"):
                grid_sec = results_grid()
                lbl_Lsec = result_row(grid_sec, "Inductance")
                lbl_Csec = result_row(grid_sec, "Self-capacitance")
                lbl_fsec = result_row(grid_sec, "Bare frequency")
                lbl_fsys = result_row(grid_sec, "System frequency")

            # Primary section
            with section_card("Primary Results", "track_changes"):
                grid_pri = results_grid()
                lbl_Lpri = result_row(grid_pri, "Total inductance")
                lbl_fpri = result_row(grid_pri, "Resonant frequency")
                lbl_tune = result_row(grid_pri, "Tuning ratio")

            # Coupling section
            with section_card("Coupling & Tuning", "link"):
                grid_cpl = results_grid()
                lbl_k = result_row(grid_cpl, "Coupling k")

            # Export bar
            with ui.card().classes("w-full").style(
                f"background: {SURFACE}; border: 1px solid {SURFACE_BORDER}; "
                f"border-radius: 8px; padding: 16px;"
            ):
                ui.label("Export").classes("text-sm font-semibold mb-2").style(
                    f"color: {TEXT};"
                )

                text_area = ui.textarea(
                    label="Output",
                    value="Click an export button to populate.",
                ).classes("w-full font-mono text-xs").props("autogrow rows=12 readonly")

                def _do_text():
                    from pyteslacoil.export.consolidated import to_text
                    text_area.value = to_text(state.design, state.outputs)

                def _do_json():
                    from pyteslacoil.export.json_export import to_json
                    text_area.value = to_json(state.design, state.outputs)

                def _do_pdf():
                    try:
                        from pyteslacoil.export.pdf_export import to_pdf_bytes
                        pdf_bytes = to_pdf_bytes(state.design, state.outputs)
                        ui.download(pdf_bytes, "pyteslacoil_export.pdf")
                    except Exception as exc:
                        ui.notify(f"PDF export failed: {exc}", type="warning")

                with ui.row().classes("gap-3 mt-3"):
                    ui.button("Export Text", icon="description", on_click=_do_text).style(
                        f"background: {ACCENT}; color: #0f1117; border-radius: 6px;"
                    )
                    ui.button("Export JSON", icon="data_object", on_click=_do_json).style(
                        f"background: transparent; border: 1px solid {ACCENT}; "
                        f"color: {ACCENT}; border-radius: 6px;"
                    )
                    ui.button("Export PDF", icon="picture_as_pdf", on_click=_do_pdf).style(
                        f"background: transparent; border: 1px solid {ACCENT}; "
                        f"color: {ACCENT}; border-radius: 6px;"
                    )

        # ── Visualizer ─────────────────────────────────────────────
        with ui.column().classes("flex-[4] min-w-[300px]"):
            with section_card("Coil Cross-Section", "straighten"):
                svg_holder = ui.html("").classes("w-full")

    # ── Reactive refresh ───────────────────────────────────────────
    def _refresh(_state: AppState):
        out = _state.outputs

        # Headline metrics
        if out.system_resonant_frequency_khz:
            freq_val.text = f"{out.system_resonant_frequency_khz:.2f}"
        if out.coupling:
            k = out.coupling.coupling_coefficient
            k_val.text = f"{k:.4f}"
            lbl_k.text = f"{k:.4f}"
            lbl_k.style(f"color: {_quality(k)} !important;")
        if out.estimated_spark_length_m:
            spark_val.text = f"{out.estimated_spark_length_in:.1f}"

        # Secondary
        if out.secondary:
            lbl_Lsec.text = f"{out.secondary.inductance_mh:.3f} mH"
            lbl_Csec.text = f"{out.secondary.self_capacitance_pf:.2f} pF"
            lbl_fsec.text = f"{out.secondary.resonant_frequency_khz:.2f} kHz"
        if out.system_resonant_frequency_khz:
            lbl_fsys.text = f"{out.system_resonant_frequency_khz:.2f} kHz"

        # Primary
        if out.primary:
            lbl_Lpri.text = f"{out.primary.total_inductance_uh:.2f} \u00b5H"
            lbl_fpri.text = f"{out.primary.resonant_frequency_khz:.2f} kHz"
        if out.tuning_ratio:
            lbl_tune.text = f"{out.tuning_ratio:.3f}"

        # Visualizer
        svg_holder.content = build_visualizer(_state)

    state.subscribe(_refresh)
    state.recalculate()
