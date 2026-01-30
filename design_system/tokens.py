"""
Design tokens for QualCoder Design System.

Single source of truth for colors, spacing, typography, and layout.

Design Philosophy:
- Scholarly & trustworthy aesthetic for qualitative research
- Ink-inspired accent colors that evoke annotation/highlighting
- Warm, paper-like surfaces that feel approachable
- Strong focus hierarchy through typography and spacing
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ColorPalette:
    """Color palette for the design system."""

    # Primary Colors - Deep Indigo (scholarly, trustworthy)
    primary: str
    primary_light: str
    primary_dark: str
    primary_foreground: str

    # Secondary/Accent Colors - Warm Coral (highlighting, annotation)
    secondary: str
    secondary_light: str
    secondary_dark: str
    secondary_foreground: str

    # Semantic Colors
    success: str
    success_light: str
    success_foreground: str
    warning: str
    warning_light: str
    warning_foreground: str
    error: str
    error_light: str
    error_foreground: str
    info: str
    info_light: str
    info_foreground: str

    # Backgrounds & Surfaces
    background: str
    surface: str
    surface_light: str
    surface_lighter: str
    surface_elevated: str

    # Text Colors
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_hint: str

    # Borders & Dividers
    border: str
    border_light: str
    divider: str

    # Input & Focus
    input: str
    ring: str

    # Focus ring with glow effect (Prussian ink)
    ring_glow: str = "rgba(30, 58, 95, 0.25)"

    # File Type Colors (Scholar's Desk palette)
    file_text: str = "#2A6F97"      # Steel blue (info)
    file_audio: str = "#A78BFA"     # Lavender (code_purple)
    file_video: str = "#E76F51"     # Terracotta (secondary_light)
    file_image: str = "#40916C"     # Forest light (success_light)
    file_pdf: str = "#E9C46A"       # Saffron (warning)

    # Code/Highlight Colors - Ink-inspired palette for annotations
    code_yellow: str = "#FBBF24"    # Highlighter yellow
    code_red: str = "#F87171"       # Soft red
    code_green: str = "#34D399"     # Mint green
    code_purple: str = "#A78BFA"    # Lavender
    code_blue: str = "#60A5FA"      # Sky blue
    code_pink: str = "#F472B6"      # Rose
    code_orange: str = "#FB923C"    # Tangerine
    code_cyan: str = "#22D3EE"      # Cyan

    # Syntax highlighting colors (for code blocks)
    syntax_background: str = "#1A1918"   # Warm dark background
    syntax_text: str = "#FAF8F5"         # Antique white
    syntax_keyword: str = "#A78BFA"      # Lavender (code_purple)
    syntax_string: str = "#34D399"       # Mint green (code_green)
    syntax_function: str = "#60A5FA"     # Sky blue (code_blue)
    syntax_class: str = "#FBBF24"        # Yellow (code_yellow)
    syntax_number: str = "#FB923C"       # Tangerine (code_orange)
    syntax_comment: str = "#78716C"      # Stone-500 (muted)

    # Gradient stops for advanced effects
    gradient_start: str = ""
    gradient_end: str = ""

    # Overlay colors
    overlay_light: str = "rgba(255, 255, 255, 0.8)"
    overlay_dark: str = "rgba(0, 0, 0, 0.5)"

    # Utility colors (for consistent usage outside design system)
    fallback_code_color: str = "#888888"  # Default when code color is missing
    text_on_dark: str = "#FFFFFF"         # White text on dark backgrounds
    text_on_light: str = "#000000"        # Black text on light backgrounds
    transparent: str = "transparent"      # Explicit transparent for stylesheets

    def __post_init__(self):
        if not self.gradient_start:
            self.gradient_start = self.primary
        if not self.gradient_end:
            self.gradient_end = self.secondary


@dataclass
class Shadows:
    """Shadow definitions for elevation levels."""

    # Shadow format: "offset-x offset-y blur spread color"
    none: str = "none"
    sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
    lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
    xl: str = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"

    # Colored shadows for buttons (enhanced with glow)
    # Updated for Scholar's Desk palette
    primary: str = "0 4px 14px rgba(30, 58, 95, 0.4)"           # Prussian ink
    primary_glow: str = "0 0 20px rgba(30, 58, 95, 0.3), 0 4px 14px rgba(30, 58, 95, 0.25)"
    secondary: str = "0 4px 14px rgba(200, 75, 49, 0.4)"        # Vermilion
    secondary_glow: str = "0 0 20px rgba(200, 75, 49, 0.3), 0 4px 14px rgba(200, 75, 49, 0.25)"
    error: str = "0 4px 14px rgba(155, 34, 38, 0.4)"            # Carmine
    error_glow: str = "0 0 20px rgba(155, 34, 38, 0.3), 0 4px 14px rgba(155, 34, 38, 0.25)"
    success: str = "0 4px 14px rgba(45, 106, 79, 0.4)"          # Forest
    success_glow: str = "0 0 20px rgba(45, 106, 79, 0.3), 0 4px 14px rgba(45, 106, 79, 0.25)"

    # Inset shadow for pressed states
    inset: str = "inset 0 2px 4px rgba(0, 0, 0, 0.1)"

    # Card elevation shadows
    card: str = "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)"
    card_hover: str = "0 10px 20px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08)"


@dataclass
class Gradients:
    """Gradient definitions for visual depth and emphasis."""

    # Button gradients - subtle top-to-bottom lighting effect
    # Updated for Scholar's Desk palette (Prussian ink)
    primary_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B5998, stop:1 #1E3A5F)"
    primary_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A6FA5, stop:1 #3B5998)"
    primary_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #152238, stop:1 #0D1520)"

    # Vermilion secondary
    secondary_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E76F51, stop:1 #C84B31)"
    secondary_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4A261, stop:1 #E76F51)"
    secondary_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9A3412, stop:1 #7C2D12)"

    # Carmine danger
    danger_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #AE2012, stop:1 #9B2226)"
    danger_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #C53030, stop:1 #AE2012)"
    danger_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7F1D1D, stop:1 #691A1A)"

    # Forest success
    success_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #40916C, stop:1 #2D6A4F)"
    success_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #52B788, stop:1 #40916C)"

    # Card/surface gradients - paper warmth
    surface_warm: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFCF7, stop:1 #FAF8F5)"
    surface_elevated: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFCF7, stop:1 #F5F0E8)"

    # Featured/highlight gradients - Prussian to Vermilion
    featured: str = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A5F, stop:1 #C84B31)"
    featured_subtle: str = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(30,58,95,0.1), stop:1 rgba(200,75,49,0.1))"


# Light theme - Scholar's Desk aesthetic
# Prussian ink + vermilion editorial marks + warm paper surfaces
COLORS_LIGHT = ColorPalette(
    # Primary - Prussian Ink (distinctive, scholarly)
    primary="#1E3A5F",              # Prussian blue
    primary_light="#3B5998",        # Slate ink
    primary_dark="#152238",         # Deep ink
    primary_foreground="#FFFFFF",

    # Secondary - Vermilion (editorial marks, annotation)
    secondary="#C84B31",            # Vermilion
    secondary_light="#E76F51",      # Terracotta
    secondary_dark="#9A3412",       # Burnt sienna
    secondary_foreground="#FFFFFF",

    # Semantic - Warmer, more refined
    success="#2D6A4F",              # Forest green
    success_light="#40916C",
    success_foreground="#FFFFFF",
    warning="#E9C46A",              # Saffron gold
    warning_light="#F4D35E",
    warning_foreground="#1C1917",
    error="#9B2226",                # Carmine red
    error_light="#AE2012",
    error_foreground="#FFFFFF",
    info="#2A6F97",                 # Steel blue
    info_light="#468FAF",
    info_foreground="#FFFFFF",

    # Backgrounds & Surfaces - True paper warmth
    background="#FAF8F5",           # Antique white
    surface="#FFFCF7",              # Cream
    surface_light="#F5F0E8",        # Parchment
    surface_lighter="#E8E2D9",      # Aged paper
    surface_elevated="#FFFCF7",

    # Text - Sepia-tinted for bookish feel
    text_primary="#1C1917",         # Stone-900
    text_secondary="#78716C",       # Stone-500
    text_disabled="#A8A29E",        # Stone-400
    text_hint="#D6D3D1",            # Stone-300

    # Borders - Warm undertones
    border="#E7E5E4",               # Stone-200
    border_light="#F5F5F4",         # Stone-100
    divider="#E7E5E4",

    # Input & Focus
    input="#FFFCF7",
    ring="#1E3A5F",
    ring_glow="rgba(30, 58, 95, 0.25)",
)

# Dark theme - Midnight Scholar aesthetic
# Deep blue-black surfaces with luminous ink accents
COLORS_DARK = ColorPalette(
    # Primary - Luminous ink for dark mode
    primary="#6B8CAE",              # Lighter prussian
    primary_light="#8FADC7",        # Sky ink
    primary_dark="#3B5998",         # Slate ink
    primary_foreground="#FFFFFF",

    # Secondary - Glowing vermilion
    secondary="#E76F51",            # Terracotta
    secondary_light="#F4A261",      # Sandy coral
    secondary_dark="#C84B31",       # Vermilion
    secondary_foreground="#1C1917",

    # Semantic - Luminous variants
    success="#40916C",              # Forest light
    success_light="#52B788",
    success_foreground="#1C1917",
    warning="#F4D35E",              # Bright saffron
    warning_light="#FCE588",
    warning_foreground="#1C1917",
    error="#E63946",                # Bright carmine
    error_light="#F07F87",
    error_foreground="#1C1917",
    info="#468FAF",                 # Steel blue light
    info_light="#74B3CE",
    info_foreground="#1C1917",

    # Backgrounds & Surfaces - Warm charcoal (not pure gray)
    background="#1A1918",           # Warm black
    surface="#262322",              # Dark stone
    surface_light="#3D3836",        # Charcoal
    surface_lighter="#57504C",      # Warm gray
    surface_elevated="#262322",

    # Text - Cream tones for warmth
    text_primary="#FAF8F5",         # Antique white
    text_secondary="#D6D3D1",       # Stone-300
    text_disabled="#78716C",        # Stone-500
    text_hint="#57534E",            # Stone-600

    # Borders - Warm undertones
    border="#3D3836",               # Charcoal
    border_light="#57504C",         # Warm gray
    divider="#3D3836",

    # Input & Focus
    input="#262322",
    ring="#6B8CAE",
    ring_glow="rgba(107, 140, 174, 0.3)",
)

# Default to light theme
COLORS = COLORS_LIGHT


@dataclass
class Spacing:
    """
    Spacing scale using a 4px base unit.

    Based on an 8-point grid system for visual consistency.
    """

    none: int = 0
    xs: int = 4       # Tight: icon gaps, badge padding
    sm: int = 8       # Compact: button padding, list item gaps
    md: int = 12      # Default: form field padding
    lg: int = 16      # Comfortable: card padding, section gaps
    xl: int = 24      # Spacious: modal padding, major sections
    xxl: int = 32     # Generous: page margins
    xxxl: int = 48    # Maximum: hero sections


@dataclass
class BorderRadius:
    """
    Border radius scale for consistent rounding.

    Larger radii create a softer, more approachable feel.
    """

    none: int = 0
    xs: int = 4       # Subtle: badges, small elements
    sm: int = 6       # Default: inputs, buttons
    md: int = 8       # Cards, dropdowns
    lg: int = 12      # Modals, large cards
    xl: int = 16      # Feature cards, hero elements
    xxl: int = 24     # Pill buttons, avatars
    full: int = 9999  # Circles


@dataclass
class Typography:
    """
    Typography settings optimized for readability.

    Uses Inter as primary font - modern, highly readable,
    with excellent support for UI text at small sizes.

    JetBrains Mono for code - clear distinction between similar chars.
    """

    # Font families with comprehensive fallbacks
    font_family: str = (
        "Inter, "
        "-apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, "
        "'Helvetica Neue', sans-serif"
    )

    font_family_mono: str = (
        "'JetBrains Mono', "
        "'Fira Code', "
        "'SF Mono', Menlo, Monaco, Consolas, "
        "'Liberation Mono', 'Courier New', monospace"
    )

    # Display font for headings (optional, falls back to font_family)
    font_family_display: str = (
        "'Plus Jakarta Sans', "
        "Inter, "
        "-apple-system, BlinkMacSystemFont, sans-serif"
    )

    # Font sizes - slightly larger for better readability
    text_xs: int = 11
    text_sm: int = 13
    text_base: int = 14
    text_lg: int = 16
    text_xl: int = 18
    text_2xl: int = 22
    text_3xl: int = 28
    text_4xl: int = 36

    # Font weights
    weight_light: int = 300
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700

    # Line heights (as multipliers)
    leading_none: float = 1.0
    leading_tight: float = 1.25
    leading_snug: float = 1.375
    leading_normal: float = 1.5
    leading_relaxed: float = 1.625

    # Letter spacing
    tracking_tighter: str = "-0.05em"   # For large display text
    tracking_tight: str = "-0.025em"    # For headings
    tracking_normal: str = "0"
    tracking_wide: str = "0.025em"
    tracking_wider: str = "0.05em"      # For small caps, labels

    # Additional font weight for emphasis
    weight_black: int = 900


@dataclass
class Layout:
    """Layout dimensions (in pixels)."""

    sidebar_width: int = 280
    sidebar_collapsed_width: int = 64
    panel_width: int = 320
    panel_min_width: int = 240
    panel_max_width: int = 480

    toolbar_height: int = 48
    statusbar_height: int = 28
    titlebar_height: int = 38
    menubar_height: int = 36
    tabbar_height: int = 40

    # Content constraints
    content_max_width: int = 1200
    narrow_max_width: int = 680


@dataclass
class Animation:
    """
    Animation timing tokens for consistent motion.

    Follows the principle of "quick but not jarring".
    """

    # Durations (in milliseconds)
    duration_instant: int = 50
    duration_fast: int = 100
    duration_normal: int = 200
    duration_slow: int = 300
    duration_slower: int = 500

    # Easing curves (CSS cubic-bezier)
    ease_default: str = "cubic-bezier(0.4, 0, 0.2, 1)"      # Material standard
    ease_in: str = "cubic-bezier(0.4, 0, 1, 1)"
    ease_out: str = "cubic-bezier(0, 0, 0.2, 1)"
    ease_in_out: str = "cubic-bezier(0.4, 0, 0.2, 1)"
    ease_bounce: str = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    ease_spring: str = "cubic-bezier(0.175, 0.885, 0.32, 1.275)"


@dataclass
class ZIndex:
    """Z-index scale for layering."""

    dropdown: int = 1000
    sticky: int = 1020
    fixed: int = 1030
    modal_backdrop: int = 1040
    modal: int = 1050
    popover: int = 1060
    tooltip: int = 1070
    toast: int = 1080


# Default instances
SPACING = Spacing()
RADIUS = BorderRadius()
TYPOGRAPHY = Typography()
LAYOUT = Layout()
ANIMATION = Animation()
SHADOWS = Shadows()
GRADIENTS = Gradients()
ZINDEX = ZIndex()

# Theme registry
_themes: Dict[str, ColorPalette] = {
    "light": COLORS_LIGHT,
    "dark": COLORS_DARK,
}

_current_theme: str = "light"


def get_colors() -> ColorPalette:
    """Get the current color palette."""
    return _themes[_current_theme]


def get_theme(name: str = "light") -> ColorPalette:
    """
    Get a specific theme's color palette.

    Args:
        name: Theme name ('light' or 'dark')

    Returns:
        ColorPalette for the requested theme
    """
    return _themes.get(name, COLORS_LIGHT)


def set_theme(name: str) -> None:
    """
    Set the current theme.

    Args:
        name: Theme name ('light' or 'dark')
    """
    global _current_theme, COLORS
    if name in _themes:
        _current_theme = name
        COLORS = _themes[name]


def register_theme(name: str, palette: ColorPalette) -> None:
    """
    Register a custom theme.

    Args:
        name: Unique theme name
        palette: ColorPalette instance
    """
    _themes[name] = palette


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Convert hex color to rgba string for Qt stylesheets.

    Qt stylesheets don't support #RRGGBBAA format, so use this
    function to create rgba() strings instead.

    Args:
        hex_color: Hex color string (e.g., "#1E3A5F")
        alpha: Alpha value from 0.0 to 1.0

    Returns:
        rgba string (e.g., "rgba(30, 58, 95, 0.15)")

    Usage:
        background-color: {hex_to_rgba(colors.primary, 0.15)};
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"
