"""
QualCoder v2 - Flet Design Tokens

Mirrors the CSS design system tokens from v2/mockups/css/design-system.css
for use in Flet components.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Typography:
    """Typography scale (1.333 ratio)."""

    xs: int = 12
    sm: int = 14
    base: int = 16
    lg: int = 18
    xl: int = 21
    xxl: int = 28
    xxxl: int = 38
    xxxxl: int = 50

    # Font weights
    light: str = "w300"
    regular: str = "w400"
    medium: str = "w500"
    semibold: str = "w600"
    bold: str = "w700"

    # Font families
    display: str = "Fraunces"
    body: str = "Source Serif 4"
    ui: str = "Instrument Sans"
    mono: str = "JetBrains Mono"


@dataclass(frozen=True)
class Spacing:
    """Spacing scale."""

    xs: int = 4  # space-1
    sm: int = 8  # space-2
    md: int = 12  # space-3
    lg: int = 16  # space-4
    xl: int = 24  # space-5
    xxl: int = 32  # space-6
    xxxl: int = 48  # space-8
    xxxxl: int = 64  # space-10


@dataclass(frozen=True)
class Radius:
    """Border radius scale."""

    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 20
    xxl: int = 28
    full: int = 9999


@dataclass(frozen=True)
class LightColors:
    """Light theme colors - Warm Parchment aesthetic."""

    # Primary - Deep Forest Green
    primary_50: str = "#f0f5f3"
    primary_100: str = "#dae8e2"
    primary_200: str = "#b5d1c5"
    primary_300: str = "#8ab5a3"
    primary_400: str = "#5f9580"
    primary_500: str = "#3d7a63"
    primary_600: str = "#2d5f4c"
    primary_700: str = "#1a3a2f"
    primary_800: str = "#122920"
    primary_900: str = "#0a1812"

    # Accent - Warm Coral/Terracotta
    accent_50: str = "#fef5f2"
    accent_100: str = "#fde8e1"
    accent_200: str = "#fbd0c3"
    accent_300: str = "#f5a991"
    accent_400: str = "#e07356"
    accent_500: str = "#d15a3a"
    accent_600: str = "#b84428"
    accent_700: str = "#8f3520"
    accent_800: str = "#6b2a1b"
    accent_900: str = "#4a1e14"

    # Highlight - Golden Amber
    highlight_100: str = "#fef9c3"
    highlight_200: str = "#fef08a"
    highlight_300: str = "#fde047"
    highlight_400: str = "#facc15"
    highlight_500: str = "#eab308"

    # Sage - Secondary green
    sage_100: str = "#e8eeea"
    sage_200: str = "#d1ddd5"
    sage_300: str = "#a8c4b3"
    sage_400: str = "#7d9a8a"
    sage_500: str = "#5a7768"

    # Rose - Soft accent
    rose_100: str = "#f5eded"
    rose_200: str = "#e8d8d7"
    rose_300: str = "#d4b8b5"
    rose_400: str = "#c9a9a6"
    rose_500: str = "#a88a86"

    # Neutrals - Warm stone tones
    stone_50: str = "#fafaf9"
    stone_100: str = "#f5f5f4"
    stone_200: str = "#e7e5e4"
    stone_300: str = "#d6d3d1"
    stone_400: str = "#a8a29e"
    stone_500: str = "#78716c"
    stone_600: str = "#57534e"
    stone_700: str = "#44403c"
    stone_800: str = "#292524"
    stone_900: str = "#1c1917"

    # Surfaces
    surface_ground: str = "#faf6f1"
    surface_paper: str = "#fffcf8"
    surface_card: str = "#ffffff"
    surface_border: str = "#e7e2dc"
    surface_border_subtle: str = "#f0ebe5"

    # Text
    text_primary: str = "#1c1917"
    text_secondary: str = "#57534e"
    text_tertiary: str = "#78716c"
    text_muted: str = "#a8a29e"
    text_inverse: str = "#faf6f1"


@dataclass(frozen=True)
class DarkColors:
    """Dark theme colors - Deep Study aesthetic."""

    # Primary - Muted sage green
    primary_50: str = "#1a2420"
    primary_100: str = "#243430"
    primary_200: str = "#2e443e"
    primary_300: str = "#3d5f53"
    primary_400: str = "#5f9580"
    primary_500: str = "#8ab5a3"
    primary_600: str = "#a8c9b8"
    primary_700: str = "#c5dcd0"
    primary_800: str = "#dfeee6"
    primary_900: str = "#f0f7f4"

    # Accent - Warm coral
    accent_50: str = "#2a1f1c"
    accent_100: str = "#3d2a24"
    accent_200: str = "#5c3d32"
    accent_300: str = "#8f5544"
    accent_400: str = "#e07356"
    accent_500: str = "#f5a991"
    accent_600: str = "#fbd0c3"
    accent_700: str = "#fde8e1"
    accent_800: str = "#fef5f2"
    accent_900: str = "#fffaf8"

    # Neutrals
    stone_50: str = "#1c1917"
    stone_100: str = "#292524"
    stone_200: str = "#44403c"
    stone_300: str = "#57534e"
    stone_400: str = "#78716c"
    stone_500: str = "#a8a29e"
    stone_600: str = "#d6d3d1"
    stone_700: str = "#e7e5e4"
    stone_800: str = "#f5f5f4"
    stone_900: str = "#fafaf9"

    # Surfaces
    surface_ground: str = "#1c1917"
    surface_paper: str = "#292524"
    surface_card: str = "#292524"
    surface_border: str = "#44403c"
    surface_border_subtle: str = "#373330"

    # Text
    text_primary: str = "#fafaf9"
    text_secondary: str = "#d6d3d1"
    text_tertiary: str = "#a8a29e"
    text_muted: str = "#78716c"
    text_inverse: str = "#1c1917"

    # Inherit from light for consistency
    sage_100: str = "#2a3530"
    sage_400: str = "#7d9a8a"
    rose_100: str = "#352a2a"
    rose_400: str = "#c9a9a6"
    highlight_300: str = "#fde047"


# Singleton instances
TYPOGRAPHY = Typography()
SPACING = Spacing()
RADIUS = Radius()
LIGHT = LightColors()
DARK = DarkColors()


def get_colors(dark_mode: bool = False):
    """Get the appropriate color scheme."""
    return DARK if dark_mode else LIGHT
