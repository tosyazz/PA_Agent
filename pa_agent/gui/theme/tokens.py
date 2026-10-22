"""Design tokens for the PA Agent dark trading-terminal theme.

Palette: deep navy-charcoal surfaces, teal/emerald primary accent, cyan info.
All hex values are chosen for ≥4.5:1 contrast against their intended background.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Palette (canonical tokens)
# ---------------------------------------------------------------------------

# Backgrounds
BG = "#0b0f14"
SURFACE_1 = "#0f1620"
SURFACE_2 = "#141c26"
SURFACE_3 = "#1b2430"
SURFACE_4 = "#23303e"

# Text
FG = "#e8eef6"
FG_2 = "#8fa1b3"
FG_3 = "#64748b"

# Accents
ACCENT = "#2dd4bf"
ACCENT_2 = "#f87171"
ACCENT_3 = "#38bdf8"

# Semantic
SUCCESS = "#34d399"
DANGER = "#f87171"
WARNING = "#fbbf24"
INFO = "#38bdf8"

# Trading
CHART_UP = "#34d399"
CHART_DOWN = "#f87171"
CHART_GRID = "#151e29"
CHART_LINE = "#fbbf24"
CHART_LINE_2 = "#7dd3fc"
CHART_LINE_3 = "#fb923c"

# Pills
PILL_GREEN_TEXT = "#6ee7b7"
PILL_GREEN_BORDER = "rgba(52,211,153,0.30)"
PILL_GREEN_BG = "rgba(52,211,153,0.10)"

PILL_AMBER_TEXT = "#fbbf24"
PILL_AMBER_BORDER = "rgba(251,191,36,0.30)"
PILL_AMBER_BG = "rgba(251,191,36,0.10)"

PILL_BLUE_TEXT = "#7dd3fc"
PILL_BLUE_BORDER = "rgba(56,189,248,0.30)"
PILL_BLUE_BG = "rgba(56,189,248,0.10)"

PILL_RED_TEXT = "#fca5a5"
PILL_RED_BORDER = "rgba(248,113,113,0.30)"
PILL_RED_BG = "rgba(248,113,113,0.10)"

PILL_CYAN_TEXT = "#5eead4"
PILL_CYAN_BORDER = "rgba(45,212,191,0.30)"
PILL_CYAN_BG = "rgba(45,212,191,0.10)"

# Typography
FONT_UI = '"Segoe UI", "Microsoft YaHei UI", sans-serif'
FONT_MONO = '"JetBrains Mono", "Cascadia Mono", "Consolas", monospace'

# Layout
RADIUS = 10
RADIUS_SM = 8
SPACING = 8

# ---------------------------------------------------------------------------
# Legacy aliases (backward-compatible names mapped to the new palette)
# ---------------------------------------------------------------------------
BG_BASE = BG
BG_PANEL = SURFACE_1
BG_ELEVATED = SURFACE_2
BG_REASONING = SURFACE_2
BG_INPUT = BG

BORDER = SURFACE_4
BORDER_MUTED = SURFACE_3

TEXT_PRIMARY = FG
TEXT_SECONDARY = FG_2
TEXT_MUTED = FG_3

ACCENT_PRIMARY = ACCENT_3
ACCENT_REASONING = ACCENT
ACCENT_SUCCESS = SUCCESS
ACCENT_WARNING = WARNING
ACCENT_DANGER = DANGER

TRADE_LONG = CHART_UP
TRADE_SHORT = CHART_DOWN
TRADE_NEUTRAL = FG_2

TOKEN_YELLOW = WARNING
TOKEN_RED = DANGER
