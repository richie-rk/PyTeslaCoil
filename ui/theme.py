# PyTeslaCoil design tokens — sourced from DESIGN.md (Google Stitch).

# ── Palette ──────────────────────────────────────────────────────────
BG = "#0f1117"
SURFACE = "#1a1d27"
SURFACE_BORDER = "#2a2d37"
SURFACE_ELEVATED = "#22252f"
INPUT_BG = "#141620"

ACCENT = "#4ecdc4"
ACCENT_WARN = "#ff6b35"
ACCENT_INFO = "#7c6df0"

TEXT = "#e8e8e8"
TEXT_DIM = "#8b8d97"
TEXT_MUTED = "#5a5d67"

GOOD = "#4ecdc4"
WARN = "#ff6b35"
BAD = "#ff4757"

# Coil visualizer component colors
VIS_SECONDARY = "#d4a06a"
VIS_PRIMARY = "#4ecdc4"
VIS_TOPLOAD = "#8892a0"
VIS_GROUND = "#3a3d4a"
VIS_DIAGRAM_BG = "#141620"
VIS_GRID = "#1e2030"

# ── Fonts ────────────────────────────────────────────────────────────
FONT_STACK = "Inter, system-ui, -apple-system, sans-serif"
MONO_STACK = "'JetBrains Mono', 'Fira Code', monospace"

# ── Reusable CSS class strings ───────────────────────────────────────
CARD_CLASS = "w-full"
CARD_STYLE = (
    f"background: {SURFACE}; border: 1px solid {SURFACE_BORDER}; "
    f"border-radius: 8px; padding: 24px;"
)

LABEL_CLASS = "text-xs uppercase tracking-wider"
LABEL_STYLE = f"color: {TEXT_DIM}; font-family: {FONT_STACK}; letter-spacing: 0.05em;"

VALUE_CLASS = "text-xl font-bold"
VALUE_STYLE = f"color: {ACCENT}; font-family: {MONO_STACK};"

SECTION_TITLE_CLASS = "text-lg font-semibold"
SECTION_TITLE_STYLE = f"color: {TEXT}; font-family: {FONT_STACK};"

INPUT_STYLE = (
    f"background: {INPUT_BG}; border: 1px solid {SURFACE_BORDER}; "
    f"border-radius: 6px; color: {TEXT};"
)

# ── Global CSS injected into <head> ─────────────────────────────────
GLOBAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

body {{
    background: {BG} !important;
    font-family: {FONT_STACK};
    color: {TEXT};
}}

/* NiceGUI / Quasar dark-mode overrides */
.q-tab {{
    color: {TEXT_DIM} !important;
    text-transform: none !important;
    font-family: {FONT_STACK} !important;
    font-size: 14px !important;
}}
.q-tab--active {{
    color: {TEXT} !important;
}}
.q-tabs__content {{
    border-bottom: 1px solid {SURFACE_BORDER} !important;
}}
.q-tab-panel {{
    padding: 24px 0 !important;
}}
.q-tab__indicator {{
    background: {ACCENT} !important;
    height: 2px !important;
}}

/* Card overrides */
.q-card {{
    background: {SURFACE} !important;
    border: 1px solid {SURFACE_BORDER} !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}}

/* Input field overrides */
.q-field__control {{
    background: {INPUT_BG} !important;
    border-radius: 6px !important;
}}
.q-field__label {{
    color: {TEXT_DIM} !important;
    font-family: {FONT_STACK} !important;
}}
.q-field--focused .q-field__control {{
    border: 1px solid {ACCENT} !important;
}}
.q-field__native, .q-field__input {{
    color: {TEXT} !important;
    font-family: {FONT_STACK} !important;
}}

/* Select / dropdown overrides */
.q-menu {{
    background: {SURFACE_ELEVATED} !important;
    border: 1px solid {SURFACE_BORDER} !important;
}}
.q-item {{
    color: {TEXT} !important;
}}
.q-item--active {{
    color: {ACCENT} !important;
}}

/* Button overrides */
.q-btn--flat {{
    color: {ACCENT} !important;
}}

/* Header */
.q-header {{
    background: {SURFACE} !important;
    border-bottom: 1px solid {SURFACE_BORDER} !important;
}}

/* Notification overrides */
.q-notification {{
    font-family: {FONT_STACK} !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}
::-webkit-scrollbar-track {{
    background: {BG};
}}
::-webkit-scrollbar-thumb {{
    background: {SURFACE_BORDER};
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {TEXT_MUTED};
}}

/* Dialog overrides */
.q-dialog__inner > .q-card {{
    background: {SURFACE_ELEVATED} !important;
}}
"""
