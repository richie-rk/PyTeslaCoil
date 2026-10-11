"""Primary coil tab: geometry, conductor, tank capacitor and auto-tune."""

from __future__ import annotations

from nicegui import ui

from pyteslacoil.engine.primary import detect_primary_geometry
from pyteslacoil.models import ConductorType, PrimaryGeometry, PrimaryInput
from pyteslacoil.ui.components.cards import clear_rows, fmt, result_rows, results_grid, section_card
from pyteslacoil.ui.components.inputs import (
    ErrorLabel,
    length_input,
    meters,
    number_input,
    on_change,
    value_of,
)
from pyteslacoil.ui.defaults import default_primary
from pyteslacoil.ui.state import AppState
from pyteslacoil.ui.theme import (
    FIELD_COLUMN_CLASS,
    INPUT_COLUMN_CLASS,
    OUTLINE_BUTTON_STYLE,
    RESULT_COLUMN_CLASS,
    TAB_ROW_CLASS,
)
from pyteslacoil.units import farads_to_nf, length_in, length_symbol, nf_to_farads

GEOMETRIES = {"flat": "Flat spiral", "helical": "Helical", "conical": "Conical"}
CONDUCTORS = {
    ConductorType.ROUND: "Round wire",
    ConductorType.TUBE: "Copper tube",
    ConductorType.RIBBON: "Ribbon",
}


def _geometry_key(primary: PrimaryInput) -> str:
    geometry = detect_primary_geometry(primary)
    if geometry == PrimaryGeometry.FLAT_SPIRAL:
        return "flat"
    if geometry == PrimaryGeometry.HELICAL:
        return "helical"
    return "conical"


def _inputs(state: AppState) -> None:
    pri = state.design.primary or default_primary()
    unit = state.design.unit_system.value

    with ui.row().classes("w-full gap-4 flex-wrap"):
        with ui.column().classes(FIELD_COLUMN_CLASS):
            geometry = ui.select(GEOMETRIES, value=_geometry_key(pri), label="Primary type").classes(
                "w-full"
            )
            r1 = length_input("Start (inner) radius", pri.radius_1, unit, step=0.05)
            r2 = length_input("End (outer) radius", pri.radius_2, unit, step=0.05)
            r2.bind_visibility_from(geometry, "value", backward=lambda v: v != "helical")
            h1 = length_input("Start height", pri.height_1, unit, step=0.05)
            h2 = length_input("End height", pri.height_2, unit, step=0.05)
            h2.bind_visibility_from(geometry, "value", backward=lambda v: v != "flat")
            turns = number_input("Turns", pri.turns, step=0.1, decimals=4, minimum=0.1)

        with ui.column().classes(FIELD_COLUMN_CLASS):
            conductor = ui.select(CONDUCTORS, value=pri.conductor_type, label="Conductor").classes(
                "w-full"
            )
            wire_d = length_input("Conductor diameter", pri.wire_diameter, unit, step=0.005, decimals=4)
            ribbon_w = length_input(
                "Ribbon width", pri.ribbon_width or pri.wire_diameter, unit, step=0.01, decimals=4
            )
            ribbon_t = length_input(
                "Ribbon thickness",
                pri.ribbon_thickness or 0.1 * pri.wire_diameter,
                unit,
                step=0.001,
                decimals=4,
            )
            for widget in (ribbon_w, ribbon_t):
                widget.bind_visibility_from(
                    conductor, "value", backward=lambda v: v == ConductorType.RIBBON
                )
            cap = number_input(
                "Tank capacitance (nF)", farads_to_nf(pri.capacitance), step=0.1, decimals=3
            )
            lead_len = length_input("Lead length (total)", pri.lead_length, unit, step=1.0, decimals=2)
            lead_d = length_input("Lead diameter", pri.lead_diameter, unit, step=0.01, decimals=4)

    auto = ui.checkbox("Auto-tune: tap the primary where it matches the secondary", value=state.design.auto_tune)
    errors = ErrorLabel()

    def apply() -> None:
        try:
            new_r1, new_h1 = meters(r1, unit), meters(h1, unit)
            new_r2 = new_r1 if geometry.value == "helical" else meters(r2, unit)
            new_h2 = new_h1 if geometry.value == "flat" else meters(h2, unit)
            ribbon = conductor.value == ConductorType.RIBBON
            new = PrimaryInput(
                radius_1=new_r1,
                radius_2=new_r2,
                height_1=new_h1,
                height_2=new_h2,
                turns=value_of(turns),
                wire_diameter=meters(wire_d, unit),
                capacitance=nf_to_farads(value_of(cap)),
                lead_length=meters(lead_len, unit),
                lead_diameter=meters(lead_d, unit),
                conductor_type=conductor.value,
                ribbon_width=meters(ribbon_w, unit) if ribbon else None,
                ribbon_thickness=meters(ribbon_t, unit) if ribbon else None,
            )
        except ValueError as exc:
            errors.show(exc)
            return
        errors.clear()
        state.set_section("primary", new)

    def set_auto_tune() -> None:
        state.set_section("auto_tune", bool(auto.value))

    on_change(
        (geometry, r1, r2, h1, h2, turns, conductor, wire_d, ribbon_w, ribbon_t, cap, lead_len, lead_d),
        apply,
    )
    on_change((auto,), set_auto_tune)


def render(state: AppState) -> None:
    with ui.row().classes(TAB_ROW_CLASS):
        with ui.column().classes(INPUT_COLUMN_CLASS):
            with section_card("Primary Coil Design", "track_changes"):
                inputs = ui.refreshable(_inputs)
                inputs(state)

        with ui.column().classes(RESULT_COLUMN_CLASS):
            with section_card("Results", "assessment"):
                rows = result_rows(
                    results_grid(),
                    {
                        "L": "Coil inductance",
                        "Ll": "Lead inductance",
                        "Ltot": "Total inductance",
                        "f": "Resonant freq",
                        "tune": "Tuning ratio (f_sec / f_pri)",
                        "Z": "Impedance",
                        "rdc": "DC resistance",
                        "wire": "Conductor length",
                        "geom": "Geometry",
                        "tuned": "Auto-tuned turns",
                    },
                )
                apply_tuned = ui.button("Use the auto-tuned geometry", icon="done").style(
                    OUTLINE_BUTTON_STYLE
                )

    def use_tuned() -> None:
        tuned = state.outputs.tuned_primary
        if tuned is not None:
            state.apply_section("primary", tuned)
            ui.notify(f"Primary set to {tuned.turns:.4f} turns", type="positive")

    apply_tuned.on_click(use_tuned)

    def refresh(s: AppState) -> None:
        out = s.outputs.primary
        tuned = s.outputs.tuned_primary
        apply_tuned.set_visibility(tuned is not None)
        if out is None:
            clear_rows(rows)
            return
        rows["L"].text = f"{out.inductance_uh:.2f} µH"
        rows["Ll"].text = f"{out.lead_inductance_uh:.2f} µH"
        rows["Ltot"].text = f"{out.total_inductance_uh:.2f} µH"
        rows["f"].text = f"{out.resonant_frequency_khz:.2f} kHz"
        rows["tune"].text = fmt(out.tuning_ratio, ".3f")
        rows["Z"].text = f"{out.impedance_ohms:,.1f} Ω"
        rows["rdc"].text = f"{out.dc_resistance_ohms:.4f} Ω"
        rows["wire"].text = f"{out.wire_length_m:.2f} m  ({out.wire_length_ft:.2f} ft)"
        rows["geom"].text = out.primary_geometry.value
        if tuned is None:
            rows["tuned"].text = "off" if not s.design.auto_tune else "failed"
        else:
            unit = s.design.unit_system.value
            end = tuned.radius_2 if out.primary_geometry == PrimaryGeometry.FLAT_SPIRAL else tuned.height_2
            rows["tuned"].text = (
                f"{tuned.turns:.4f} (ends at {length_in(end, unit):.3f} {length_symbol(unit)})"
            )

    state.on_design_replaced(lambda _s: inputs.refresh())
    state.subscribe(refresh)
