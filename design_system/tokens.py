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

    # Focus ring with glow effect
    ring_glow: str = "rgba(79, 70, 229, 0.25)"

    # File Type Colors (distinctive, accessible)
    file_text: str = "#3B82F6"      # Blue
    file_audio: str = "#8B5CF6"     # Violet
    file_video: str = "#EC4899"     # Pink
    file_image: str = "#10B981"     # Emerald
    file_pdf: str = "#F59E0B"       # Amber

    # Code/Highlight Colors - Ink-inspired palette for annotations
    code_yellow: str = "#FBBF24"    # Highlighter yellow
    code_red: str = "#F87171"       # Soft red
    code_green: str = "#34D399"     # Mint green
    code_purple: str = "#A78BFA"    # Lavender
    code_blue: str = "#60A5FA"      # Sky blue
    code_pink: str = "#F472B6"      # Rose
    code_orange: str = "#FB923C"    # Tangerine
    code_cyan: str = "#22D3EE"      # Cyan

    # Gradient stops for advanced effects
    gradient_start: str = ""
    gradient_end: str = ""

    # Overlay colors
    overlay_light: str = "rgba(255, 255, 255, 0.8)"
    overlay_dark: str = "rgba(0, 0, 0, 0.5)"

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
    primary: str = "0 4px 14px rgba(79, 70, 229, 0.4)"
    primary_glow: str = "0 0 20px rgba(79, 70, 229, 0.3), 0 4px 14px rgba(79, 70, 229, 0.25)"
    secondary: str = "0 4px 14px rgba(249, 115, 22, 0.4)"
    secondary_glow: str = "0 0 20px rgba(249, 115, 22, 0.3), 0 4px 14px rgba(249, 115, 22, 0.25)"
    error: str = "0 4px 14px rgba(239, 68, 68, 0.4)"
    error_glow: str = "0 0 20px rgba(239, 68, 68, 0.3), 0 4px 14px rgba(239, 68, 68, 0.25)"
    success: str = "0 4px 14px rgba(16, 185, 129, 0.4)"
    success_glow: str = "0 0 20px rgba(16, 185, 129, 0.3), 0 4px 14px rgba(16, 185, 129, 0.25)"

    # Inset shadow for pressed states
    inset: str = "inset 0 2px 4px rgba(0, 0, 0, 0.1)"

    # Card elevation shadows
    card: str = "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)"
    card_hover: str = "0 10px 20px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08)"


@dataclass
class Gradients:
    """Gradient definitions for visual depth and emphasis."""

    # Button gradients - subtle top-to-bottom lighting effect
    primary_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6366F1, stop:1 #4F46E5)"
    primary_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #818CF8, stop:1 #6366F1)"
    primary_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4338CA, stop:1 #3730A3)"

    secondary_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FB923C, stop:1 #F97316)"
    secondary_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FDBA74, stop:1 #FB923C)"
    secondary_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EA580C, stop:1 #C2410C)"

    danger_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F87171, stop:1 #EF4444)"
    danger_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FCA5A5, stop:1 #F87171)"
    danger_button_pressed: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #DC2626, stop:1 #B91C1C)"

    success_button: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34D399, stop:1 #10B981)"
    success_button_hover: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6EE7B7, stop:1 #34D399)"

    # Card/surface gradients - subtle warmth
    surface_warm: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #FAFAF9)"
    surface_elevated: str = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F9FAFB)"

    # Featured/highlight gradients
    featured: str = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4F46E5, stop:1 #F97316)"
    featured_subtle: str = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(79,70,229,0.1), stop:1 rgba(249,115,22,0.1))"


# Light theme - Warm paper aesthetic
COLORS_LIGHT = ColorPalette(
    # Primary - Deep Indigo (scholarly, authoritative)
    primary="#4F46E5",
    primary_light="#818CF8",
    primary_dark="#3730A3",
    primary_foreground="#FFFFFF",

    # Secondary - Warm Coral (annotation, highlighting)
    secondary="#F97316",
    secondary_light="#FB923C",
    secondary_dark="#EA580C",
    secondary_foreground="#FFFFFF",

    # Semantic - Softer, more refined
    success="#10B981",
    success_light="#34D399",
    success_foreground="#FFFFFF",
    warning="#F59E0B",
    warning_light="#FBBF24",
    warning_foreground="#1F2937",
    error="#EF4444",
    error_light="#F87171",
    error_foreground="#FFFFFF",
    info="#3B82F6",
    info_light="#60A5FA",
    info_foreground="#FFFFFF",

    # Backgrounds & Surfaces - Warm paper tones
    background="#F9FAFB",           # Slightly warm white
    surface="#FFFFFF",
    surface_light="#F3F4F6",        # Light gray with warmth
    surface_lighter="#E5E7EB",
    surface_elevated="#FFFFFF",

    # Text - Softer blacks for readability
    text_primary="#111827",         # Near black, not pure
    text_secondary="#6B7280",       # Warm gray
    text_disabled="#9CA3AF",
    text_hint="#D1D5DB",

    # Borders - Subtle, refined
    border="#E5E7EB",
    border_light="#F3F4F6",
    divider="#E5E7EB",

    # Input & Focus
    input="#F9FAFB",
    ring="#4F46E5",
    ring_glow="rgba(79, 70, 229, 0.25)",
)

# Dark theme - Deep, focused aesthetic
COLORS_DARK = ColorPalette(
    # Primary - Lighter indigo for dark mode
    primary="#818CF8",
    primary_light="#A5B4FC",
    primary_dark="#6366F1",
    primary_foreground="#FFFFFF",

    # Secondary - Warmer orange
    secondary="#FB923C",
    secondary_light="#FDBA74",
    secondary_dark="#F97316",
    secondary_foreground="#1F2937",

    # Semantic
    success="#34D399",
    success_light="#6EE7B7",
    success_foreground="#1F2937",
    warning="#FBBF24",
    warning_light="#FCD34D",
    warning_foreground="#1F2937",
    error="#F87171",
    error_light="#FCA5A5",
    error_foreground="#1F2937",
    info="#60A5FA",
    info_light="#93C5FD",
    info_foreground="#1F2937",

    # Backgrounds & Surfaces - Deep, rich darks
    background="#111827",
    surface="#1F2937",
    surface_light="#374151",
    surface_lighter="#4B5563",
    surface_elevated="#1F2937",

    # Text - High contrast for dark mode
    text_primary="#F9FAFB",
    text_secondary="#D1D5DB",
    text_disabled="#6B7280",
    text_hint="#4B5563",

    # Borders
    border="#374151",
    border_light="#4B5563",
    divider="#374151",

    # Input & Focus
    input="#1F2937",
    ring="#818CF8",
    ring_glow="rgba(129, 140, 248, 0.3)",
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
