"""
Qt-Material Theme Integration for QualCoder Design System.

Provides Material Design theming via qt-material library with
integration to our token system.

Usage:
    from design_system.theme import setup_theme, get_material_palette

    app = QApplication(sys.argv)
    setup_theme(app, theme='dark_teal')

    # Access colors
    palette = get_material_palette()
    print(palette.primary)  # '#009688'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from .qt_compat import QApplication

# Try to import qt-material, fall back gracefully
try:
    from qt_material import apply_stylesheet, list_themes
    HAS_QT_MATERIAL = True
except ImportError:
    HAS_QT_MATERIAL = False
    warnings.warn(
        "qt-material not installed. Install with: pip install qt-material",
        ImportWarning,
    )


# Qt-Material theme color mappings
# These are extracted from qt-material's XML theme files
MATERIAL_THEMES: Dict[str, Dict[str, str]] = {
    'dark_teal': {
        'primary': '#009688',
        'primary_light': '#4db6ac',
        'primary_dark': '#00796b',
        'secondary': '#ff5722',
        'secondary_light': '#ff8a65',
        'secondary_dark': '#e64a19',
        'background': '#1e1e1e',
        'surface': '#2d2d2d',
        'surface_light': '#3d3d3d',
        'surface_lighter': '#4d4d4d',
        'text_primary': '#ffffff',
        'text_secondary': '#b0b0b0',
        'text_disabled': '#707070',
        'border': '#404040',
        'error': '#f44336',
        'warning': '#ff9800',
        'success': '#4caf50',
        'info': '#2196f3',
    },
    'light_teal': {
        'primary': '#009688',
        'primary_light': '#4db6ac',
        'primary_dark': '#00796b',
        'secondary': '#ff5722',
        'secondary_light': '#ff8a65',
        'secondary_dark': '#e64a19',
        'background': '#fafafa',
        'surface': '#ffffff',
        'surface_light': '#f5f5f5',
        'surface_lighter': '#eeeeee',
        'text_primary': '#212121',
        'text_secondary': '#757575',
        'text_disabled': '#9e9e9e',
        'border': '#e0e0e0',
        'error': '#f44336',
        'warning': '#ff9800',
        'success': '#4caf50',
        'info': '#2196f3',
    },
    'dark_amber': {
        'primary': '#ffc107',
        'primary_light': '#ffd54f',
        'primary_dark': '#ff8f00',
        'secondary': '#ff5722',
        'secondary_light': '#ff8a65',
        'secondary_dark': '#e64a19',
        'background': '#1e1e1e',
        'surface': '#2d2d2d',
        'surface_light': '#3d3d3d',
        'surface_lighter': '#4d4d4d',
        'text_primary': '#ffffff',
        'text_secondary': '#b0b0b0',
        'text_disabled': '#707070',
        'border': '#404040',
        'error': '#f44336',
        'warning': '#ff9800',
        'success': '#4caf50',
        'info': '#2196f3',
    },
    'dark_blue': {
        'primary': '#2196f3',
        'primary_light': '#64b5f6',
        'primary_dark': '#1976d2',
        'secondary': '#ff5722',
        'secondary_light': '#ff8a65',
        'secondary_dark': '#e64a19',
        'background': '#1e1e1e',
        'surface': '#2d2d2d',
        'surface_light': '#3d3d3d',
        'surface_lighter': '#4d4d4d',
        'text_primary': '#ffffff',
        'text_secondary': '#b0b0b0',
        'text_disabled': '#707070',
        'border': '#404040',
        'error': '#f44336',
        'warning': '#ff9800',
        'success': '#4caf50',
        'info': '#2196f3',
    },
    'dark_purple': {
        'primary': '#9c27b0',
        'primary_light': '#ba68c8',
        'primary_dark': '#7b1fa2',
        'secondary': '#ff5722',
        'secondary_light': '#ff8a65',
        'secondary_dark': '#e64a19',
        'background': '#1e1e1e',
        'surface': '#2d2d2d',
        'surface_light': '#3d3d3d',
        'surface_lighter': '#4d4d4d',
        'text_primary': '#ffffff',
        'text_secondary': '#b0b0b0',
        'text_disabled': '#707070',
        'border': '#404040',
        'error': '#f44336',
        'warning': '#ff9800',
        'success': '#4caf50',
        'info': '#2196f3',
    },
}

# Default theme
DEFAULT_THEME = 'dark_teal'

# Current active theme
_current_theme: Optional[str] = None
_current_palette: Optional['MaterialPalette'] = None


@dataclass
class MaterialPalette:
    """Material Design color palette from qt-material theme."""

    # Primary colors (required)
    primary: str
    primary_light: str
    primary_dark: str

    # Secondary colors (required)
    secondary: str
    secondary_light: str
    secondary_dark: str

    # Foreground colors (with defaults)
    primary_foreground: str = '#ffffff'
    secondary_foreground: str = '#ffffff'

    # Semantic colors
    error: str = '#f44336'
    error_light: str = '#e57373'
    error_foreground: str = '#ffffff'
    warning: str = '#ff9800'
    warning_light: str = '#ffb74d'
    warning_foreground: str = '#212121'
    success: str = '#4caf50'
    success_light: str = '#81c784'
    success_foreground: str = '#ffffff'
    info: str = '#2196f3'
    info_light: str = '#64b5f6'
    info_foreground: str = '#ffffff'

    # Background & surfaces
    background: str = '#1e1e1e'
    surface: str = '#2d2d2d'
    surface_light: str = '#3d3d3d'
    surface_lighter: str = '#4d4d4d'
    surface_elevated: str = '#3d3d3d'

    # Text colors
    text_primary: str = '#ffffff'
    text_secondary: str = '#b0b0b0'
    text_disabled: str = '#707070'
    text_hint: str = '#606060'

    # Borders
    border: str = '#404040'
    border_light: str = '#505050'
    divider: str = '#404040'

    # Input & focus
    input: str = '#3d3d3d'
    ring: str = '#009688'

    # File type colors (consistent across themes)
    file_text: str = '#2196f3'
    file_audio: str = '#9c27b0'
    file_video: str = '#f44336'
    file_image: str = '#4caf50'
    file_pdf: str = '#ff5722'

    # Code highlight colors
    code_yellow: str = '#ffc107'
    code_red: str = '#f44336'
    code_green: str = '#4caf50'
    code_purple: str = '#9c27b0'
    code_blue: str = '#2196f3'
    code_pink: str = '#e91e63'
    code_orange: str = '#ff9800'
    code_cyan: str = '#00bcd4'

    @classmethod
    def from_theme(cls, theme_name: str) -> 'MaterialPalette':
        """Create palette from a theme name."""
        theme_data = MATERIAL_THEMES.get(theme_name, MATERIAL_THEMES[DEFAULT_THEME])

        return cls(
            primary=theme_data['primary'],
            primary_light=theme_data['primary_light'],
            primary_dark=theme_data['primary_dark'],
            secondary=theme_data['secondary'],
            secondary_light=theme_data['secondary_light'],
            secondary_dark=theme_data['secondary_dark'],
            background=theme_data['background'],
            surface=theme_data['surface'],
            surface_light=theme_data['surface_light'],
            surface_lighter=theme_data['surface_lighter'],
            text_primary=theme_data['text_primary'],
            text_secondary=theme_data['text_secondary'],
            text_disabled=theme_data['text_disabled'],
            border=theme_data['border'],
            error=theme_data['error'],
            warning=theme_data['warning'],
            success=theme_data['success'],
            info=theme_data['info'],
            ring=theme_data['primary'],
        )


def setup_theme(
    app: 'QApplication',
    theme: str = DEFAULT_THEME,
    extra: Optional[Dict[str, str]] = None,
    invert_secondary: bool = False,
) -> MaterialPalette:
    """
    Apply qt-material theme to the application.

    Args:
        app: QApplication instance
        theme: Theme name (e.g., 'dark_teal', 'light_teal', 'dark_amber')
        extra: Extra stylesheet variables to override
        invert_secondary: Whether to invert secondary color

    Returns:
        MaterialPalette with the theme colors

    Example:
        app = QApplication(sys.argv)
        palette = setup_theme(app, 'dark_teal')
    """
    global _current_theme, _current_palette

    _current_theme = theme
    _current_palette = MaterialPalette.from_theme(theme)

    if HAS_QT_MATERIAL:
        # Map our theme names to qt-material theme names
        qt_material_theme = f'{theme}.xml'

        try:
            apply_stylesheet(
                app,
                theme=qt_material_theme,
                extra=extra,
                invert_secondary=invert_secondary,
            )
        except Exception as e:
            warnings.warn(f"Failed to apply qt-material theme: {e}")
            # Apply fallback stylesheet
            _apply_fallback_stylesheet(app, _current_palette)
    else:
        # No qt-material, use fallback
        _apply_fallback_stylesheet(app, _current_palette)

    return _current_palette


def _apply_fallback_stylesheet(app: 'QApplication', palette: MaterialPalette) -> None:
    """Apply a basic Material-like stylesheet when qt-material is unavailable."""
    stylesheet = f"""
    QWidget {{
        background-color: {palette.background};
        color: {palette.text_primary};
        font-family: 'Roboto', 'Segoe UI', sans-serif;
        font-size: 14px;
    }}

    QMainWindow, QDialog {{
        background-color: {palette.background};
    }}

    QPushButton {{
        background-color: {palette.primary};
        color: {palette.primary_foreground};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {palette.primary_light};
    }}

    QPushButton:pressed {{
        background-color: {palette.primary_dark};
    }}

    QPushButton:disabled {{
        background-color: {palette.surface_lighter};
        color: {palette.text_disabled};
    }}

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {palette.surface};
        color: {palette.text_primary};
        border: 1px solid {palette.border};
        border-radius: 4px;
        padding: 8px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {palette.primary};
    }}

    QComboBox {{
        background-color: {palette.surface};
        color: {palette.text_primary};
        border: 1px solid {palette.border};
        border-radius: 4px;
        padding: 8px;
    }}

    QScrollBar:vertical {{
        background-color: {palette.surface};
        width: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {palette.surface_lighter};
        border-radius: 6px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {palette.text_disabled};
    }}

    QTabWidget::pane {{
        border: 1px solid {palette.border};
        background-color: {palette.surface};
    }}

    QTabBar::tab {{
        background-color: {palette.surface};
        color: {palette.text_secondary};
        padding: 8px 16px;
        border-bottom: 2px solid transparent;
    }}

    QTabBar::tab:selected {{
        color: {palette.primary};
        border-bottom: 2px solid {palette.primary};
    }}

    QMenu {{
        background-color: {palette.surface};
        border: 1px solid {palette.border};
        border-radius: 4px;
    }}

    QMenu::item {{
        padding: 8px 16px;
    }}

    QMenu::item:selected {{
        background-color: {palette.surface_light};
    }}

    QToolTip {{
        background-color: {palette.surface};
        color: {palette.text_primary};
        border: 1px solid {palette.border};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """
    app.setStyleSheet(stylesheet)


def get_material_palette() -> MaterialPalette:
    """
    Get the current Material palette.

    Returns the palette from the last setup_theme() call,
    or creates a default dark_teal palette.
    """
    global _current_palette

    if _current_palette is None:
        _current_palette = MaterialPalette.from_theme(DEFAULT_THEME)

    return _current_palette


def get_current_theme() -> str:
    """Get the current theme name."""
    return _current_theme or DEFAULT_THEME


def available_themes() -> list[str]:
    """List available theme names."""
    return list(MATERIAL_THEMES.keys())


def is_dark_theme(theme_name: Optional[str] = None) -> bool:
    """Check if a theme is a dark theme."""
    theme = theme_name or get_current_theme()
    return theme.startswith('dark_')


# Integration with existing token system
def get_colors() -> MaterialPalette:
    """
    Compatibility function for existing token system.

    Returns MaterialPalette instead of ColorPalette.
    The API is compatible.
    """
    return get_material_palette()


def get_theme(name: str = "dark") -> MaterialPalette:
    """
    Compatibility function for existing token system.

    Maps 'dark' -> 'dark_teal' and 'light' -> 'light_teal'.
    """
    theme_map = {
        'dark': 'dark_teal',
        'light': 'light_teal',
    }
    theme_name = theme_map.get(name, name)
    return MaterialPalette.from_theme(theme_name)


__all__ = [
    'setup_theme',
    'get_material_palette',
    'get_current_theme',
    'available_themes',
    'is_dark_theme',
    'MaterialPalette',
    'HAS_QT_MATERIAL',
    # Compatibility
    'get_colors',
    'get_theme',
]
