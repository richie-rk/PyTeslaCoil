from __future__ import annotations

from nicegui import ui

from ui.state import AppState
from ui.theme import (
    BAD,
    CARD_CLASS,
    GOOD,
    LABEL_CLASS,
    SECTION_TITLE_CLASS,
    VALUE_CLASS,
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

    with ui.row().classes("w-full gap-6"):
        # ----- summary numbers ------------------------------------------
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("System summary").classes(SECTION_TITLE_CLASS)
                grid = ui.grid(columns=2).classes("w-full gap-2")
                labels: dict[str, ui.label] = {}

                def _row(name, key):
                    with grid:
                        ui.label(name).classes(LABEL_CLASS)
                        labels[key] = ui.label("—").classes(VALUE_CLASS)

                _row("Secondary L", "Lsec")
                _row("Secondary C", "Csec")
                _row("Secondary f", "fsec")
                _row("System f (with topload)", "fsys")
                _row("Primary L", "Lpri")
                _row("Primary f", "fpri")
                _row("Tuning ratio", "tune")
                _row("Coupling k", "k")
                _row("Spark length", "spark")

            with ui.card().classes(CARD_CLASS + " mt-4"):
                ui.label("Consolidated text export").classes(
                    SECTION_TITLE_CLASS
                )
                text_area = ui.textarea(
                    label="Output",
                    value="Click Refresh to populate.",
                ).classes("w-full font-mono text-xs").props("autogrow rows=20 readonly")

                def _do_text():
                    from pyteslacoil.export.consolidated import to_text

                    text_area.value = to_text(state.design, state.outputs)

                def _do_json():
                    from pyteslacoil.export.json_export import to_json

                    text_area.value = to_json(state.design, state.outputs)

                def _do_pdf():
                    try:
                        from pyteslacoil.export.pdf_export import to_pdf_bytes

                        path = "pyteslacoil_export.pdf"
                        with open(path, "wb") as f:
                            f.write(to_pdf_bytes(state.design, state.outputs))
                        ui.notify(f"Wrote {path}", type="positive")
                    except Exception as exc:
                        ui.notify(f"PDF export failed: {exc}", type="warning")

                with ui.row().classes("gap-2 mt-2"):
                    ui.button("Refresh text", on_click=_do_text).props("color=cyan")
                    ui.button("As JSON", on_click=_do_json).props("flat color=cyan")
                    ui.button("Save PDF", on_click=_do_pdf).props("flat color=cyan")

        # ----- visualizer -----------------------------------------------
        with ui.column().classes("w-1/2"):
            with ui.card().classes(CARD_CLASS):
                ui.label("Coil cross-section").classes(SECTION_TITLE_CLASS)
                svg_holder = ui.html("").classes("w-full")

            def _refresh(_state: AppState):
                out = _state.outputs
                if out.secondary:
                    labels["Lsec"].text = f"{out.secondary.inductance_mh:.3f} mH"
                    labels["Csec"].text = f"{out.secondary.self_capacitance_pf:.2f} pF"
                    labels["fsec"].text = f"{out.secondary.resonant_frequency_khz:.2f} kHz"
                if out.system_resonant_frequency_khz:
                    labels["fsys"].text = f"{out.system_resonant_frequency_khz:.2f} kHz"
                if out.primary:
                    labels["Lpri"].text = f"{out.primary.total_inductance_uh:.2f} µH"
                    labels["fpri"].text = f"{out.primary.resonant_frequency_khz:.2f} kHz"
                if out.tuning_ratio:
                    labels["tune"].text = f"{out.tuning_ratio:.3f}"
                if out.coupling:
                    k = out.coupling.coupling_coefficient
                    labels["k"].text = f"{k:.4f}"
                    labels["k"].style(f"color: {_quality(k)}")
                if out.estimated_spark_length_m:
                    labels["spark"].text = (
                        f"{out.estimated_spark_length_in:.1f} in  "
                        f"({out.estimated_spark_length_m * 100:.1f} cm)"
                    )
                # Refresh visualizer.
                svg_holder.content = build_visualizer(_state)

            state.subscribe(_refresh)
            state.recalculate()
