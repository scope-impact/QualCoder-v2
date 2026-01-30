"""
Design tokens for QualCoder Design System.

Single source of truth for colors, spacing, typography, and layout.
"""

from dataclasses import dataclass


@dataclass
class ColorPalette:
    """Color palette for the design system."""

    # Primary Colors
    primary: str
    primary_light: str
    primary_dark: str
    primary_foreground: str

    # Secondary/Accent Colors
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

    # File Type Colors
    file_text: str = "#2196F3"
    file_audio: str = "#9C27B0"
    file_video: str = "#F44336"
    file_image: str = "#4CAF50"
    file_pdf: str = "#FF5722"

    # Code Highlight Colors
    code_yellow: str = "#FFC107"
    code_red: str = "#F44336"
    code_green: str = "#4CAF50"
    code_purple: str = "#9C27B0"
    code_blue: str = "#2196F3"
    code_pink: str = "#E91E63"
    code_orange: str = "#FF9800"
    code_cyan: str = "#00BCD4"


# The color palette (light theme with teal primary)
COLORS = ColorPalette(
    # Primary - Teal
    primary="#009688",
    primary_light="#4DB6AC",
    primary_dark="#00796B",
    primary_foreground="#FFFFFF",

    # Secondary - Orange
    secondary="#FF5722",
    secondary_light="#FF8A65",
    secondary_dark="#E64A19",
    secondary_foreground="#FFFFFF",

    # Semantic
    success="#4CAF50",
    success_light="#81C784",
    success_foreground="#FFFFFF",
    warning="#FF9800",
    warning_light="#FFB74D",
    warning_foreground="#212121",
    error="#F44336",
    error_light="#E57373",
    error_foreground="#FFFFFF",
    info="#2196F3",
    info_light="#64B5F6",
    info_foreground="#FFFFFF",

    # Backgrounds & Surfaces (light)
    background="#FAFAFA",
    surface="#FFFFFF",
    surface_light="#F5F5F5",
    surface_lighter="#EEEEEE",
    surface_elevated="#FFFFFF",

    # Text (dark on light)
    text_primary="#212121",
    text_secondary="#757575",
    text_disabled="#9E9E9E",
    text_hint="#BDBDBD",

    # Borders
    border="#E0E0E0",
    border_light="#EEEEEE",
    divider="#EEEEEE",

    # Input & Focus
    input="#F5F5F5",
    ring="#009688",
)


@dataclass
class Spacing:
    """Spacing scale (in pixels)."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    xxxl: int = 32


@dataclass
class BorderRadius:
    """Border radius scale (in pixels)."""

    none: int = 0
    xs: int = 4
    sm: int = 6
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclass
class Typography:
    """Typography settings."""

    font_family: str = "Roboto, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    font_family_mono: str = "Roboto Mono, Consolas, Monaco, monospace"

    # Font sizes
    text_xs: int = 10
    text_sm: int = 12
    text_base: int = 14
    text_lg: int = 16
    text_xl: int = 18
    text_2xl: int = 24
    text_3xl: int = 28

    # Font weights
    weight_light: int = 300
    weight_normal: int = 400
    weight_medium: int = 500
    weight_bold: int = 700


@dataclass
class Layout:
    """Layout dimensions (in pixels)."""

    sidebar_width: int = 300
    panel_width: int = 280
    toolbar_height: int = 52
    statusbar_height: int = 32
    titlebar_height: int = 40
    menubar_height: int = 40
    tabbar_height: int = 44


# Default instances
SPACING = Spacing()
RADIUS = BorderRadius()
TYPOGRAPHY = Typography()
LAYOUT = Layout()


def get_colors() -> ColorPalette:
    """Get the color palette."""
    return COLORS


def get_theme(name: str = "dark") -> ColorPalette:
    """Get the color palette. The name parameter is ignored (single theme)."""
    return COLORS
