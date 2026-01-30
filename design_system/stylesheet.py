"""
Stylesheet generator for PySide6.

Converts design tokens to QSS (Qt Style Sheets) with:
- Refined visual styling
- Consistent hover/focus states
- Accessible contrast ratios
- Smooth visual hierarchy
"""

from .tokens import ColorPalette, SPACING, RADIUS, TYPOGRAPHY, LAYOUT, SHADOWS


def generate_stylesheet(colors: ColorPalette) -> str:
    """
    Generate complete QSS stylesheet from design tokens.

    Args:
        colors: ColorPalette instance to use for theming

    Returns:
        Complete QSS stylesheet string
    """
    # Pre-compute some derived values
    primary_hover = _blend_colors(colors.primary, colors.primary_light, 0.5)
    secondary_hover = _blend_colors(colors.secondary, colors.secondary_light, 0.5)

    return f"""
/* =============================================================================
   QualCoder Design System - Generated Stylesheet
   ============================================================================= */

/* ===== CSS Variables (via QSS properties) ===== */
/* Note: QSS doesn't support CSS variables, but we document the token usage */

/* ===== Base Reset ===== */
* {{
    outline: none;
}}

QWidget {{
    font-family: {TYPOGRAPHY.font_family};
    font-size: {TYPOGRAPHY.text_base}px;
    color: {colors.text_primary};
    background-color: transparent;
    selection-background-color: {colors.primary};
    selection-color: {colors.primary_foreground};
}}

QMainWindow, QDialog {{
    background-color: {colors.background};
}}

/* ===== Focus Ring ===== */
/* Consistent focus indication across all interactive elements */
*:focus {{
    outline: none;
}}

/* =============================================================================
   BUTTONS
   ============================================================================= */

QPushButton {{
    background-color: {colors.primary};
    color: {colors.primary_foreground};
    border: none;
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.lg}px;
    font-size: {TYPOGRAPHY.text_sm}px;
    font-weight: {TYPOGRAPHY.weight_medium};
    min-height: 36px;
    min-width: 64px;
}}

QPushButton:hover {{
    background-color: {primary_hover};
}}

QPushButton:pressed {{
    background-color: {colors.primary_dark};
}}

QPushButton:disabled {{
    background-color: {colors.surface_lighter};
    color: {colors.text_disabled};
}}

QPushButton:focus {{
    border: 2px solid {colors.ring};
}}

/* --- Button Variants --- */

/* Secondary/Subtle Button */
QPushButton[variant="secondary"] {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
    border: none;
}}

QPushButton[variant="secondary"]:hover {{
    background-color: {colors.surface_lighter};
}}

QPushButton[variant="secondary"]:pressed {{
    background-color: {colors.border};
}}

/* Outline/Ghost Button */
QPushButton[variant="outline"] {{
    background-color: transparent;
    color: {colors.text_primary};
    border: 1px solid {colors.border};
}}

QPushButton[variant="outline"]:hover {{
    background-color: {colors.surface_light};
    border-color: {colors.primary};
    color: {colors.primary};
}}

/* Ghost Button (no border) */
QPushButton[variant="ghost"] {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
}}

QPushButton[variant="ghost"]:hover {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
}}

/* Destructive/Danger Button */
QPushButton[variant="destructive"],
QPushButton[variant="danger"] {{
    background-color: {colors.error};
    color: {colors.error_foreground};
}}

QPushButton[variant="destructive"]:hover,
QPushButton[variant="danger"]:hover {{
    background-color: {colors.error_light};
}}

/* Success Button */
QPushButton[variant="success"] {{
    background-color: {colors.success};
    color: {colors.success_foreground};
}}

QPushButton[variant="success"]:hover {{
    background-color: {colors.success_light};
}}

/* Icon-only Button */
QPushButton[variant="icon"] {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}}

QPushButton[variant="icon"]:hover {{
    background-color: {colors.surface_light};
    color: {colors.primary};
}}

/* Link-style Button */
QPushButton[variant="link"] {{
    background-color: transparent;
    color: {colors.primary};
    border: none;
    padding: 0;
    min-height: 0;
    min-width: 0;
    text-decoration: underline;
}}

QPushButton[variant="link"]:hover {{
    color: {colors.primary_dark};
}}

/* =============================================================================
   FORM INPUTS
   ============================================================================= */

QLineEdit,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox {{
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    font-size: {TYPOGRAPHY.text_base}px;
    selection-background-color: {colors.primary};
    selection-color: {colors.primary_foreground};
}}

QLineEdit:hover,
QTextEdit:hover,
QPlainTextEdit:hover {{
    border-color: {colors.text_disabled};
}}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {{
    border-color: {colors.primary};
    border-width: 2px;
    padding: {SPACING.sm - 1}px {SPACING.md - 1}px;
}}

QLineEdit:disabled,
QTextEdit:disabled {{
    background-color: {colors.surface_light};
    color: {colors.text_disabled};
    border-color: {colors.border_light};
}}

QLineEdit[error="true"] {{
    border-color: {colors.error};
    border-width: 2px;
    padding: {SPACING.sm - 1}px {SPACING.md - 1}px;
}}

/* Placeholder styling */
QLineEdit::placeholder {{
    color: {colors.text_hint};
}}

/* =============================================================================
   LABELS
   ============================================================================= */

QLabel {{
    color: {colors.text_primary};
    background-color: transparent;
}}

QLabel[variant="muted"],
QLabel[variant="secondary"] {{
    color: {colors.text_secondary};
}}

QLabel[variant="title"] {{
    font-family: {TYPOGRAPHY.font_family_display};
    font-size: {TYPOGRAPHY.text_xl}px;
    font-weight: {TYPOGRAPHY.weight_bold};
    color: {colors.text_primary};
}}

QLabel[variant="heading"] {{
    font-family: {TYPOGRAPHY.font_family_display};
    font-size: {TYPOGRAPHY.text_lg}px;
    font-weight: {TYPOGRAPHY.weight_semibold};
    color: {colors.text_primary};
}}

QLabel[variant="display"] {{
    font-family: {TYPOGRAPHY.font_family_display};
    font-size: {TYPOGRAPHY.text_2xl}px;
    font-weight: {TYPOGRAPHY.weight_bold};
    color: {colors.text_primary};
}}

QLabel[variant="description"],
QLabel[variant="hint"] {{
    color: {colors.text_secondary};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

QLabel[variant="error"] {{
    color: {colors.error};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

QLabel[variant="success"] {{
    color: {colors.success};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

/* =============================================================================
   CARDS & FRAMES
   ============================================================================= */

QFrame[variant="card"] {{
    background-color: {colors.surface};
    border: 1px solid {colors.border_light};
    border-radius: {RADIUS.lg}px;
}}

QFrame[variant="card"]:hover {{
    border-color: {colors.border};
}}

QFrame[variant="panel"] {{
    background-color: {colors.surface};
    border-right: 1px solid {colors.border};
}}

QFrame[variant="elevated"] {{
    background-color: {colors.surface_elevated};
    border: none;
    border-radius: {RADIUS.lg}px;
}}

/* =============================================================================
   COMBO BOX / SELECT
   ============================================================================= */

QComboBox {{
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    padding-right: {SPACING.xxl}px;
    font-size: {TYPOGRAPHY.text_base}px;
    min-height: 36px;
}}

QComboBox:hover {{
    border-color: {colors.text_disabled};
}}

QComboBox:focus {{
    border-color: {colors.primary};
    border-width: 2px;
    padding: {SPACING.sm - 1}px {SPACING.md - 1}px;
    padding-right: {SPACING.xxl - 1}px;
}}

QComboBox:disabled {{
    background-color: {colors.surface_light};
    color: {colors.text_disabled};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: {SPACING.sm}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors.text_secondary};
}}

QComboBox::down-arrow:hover {{
    border-top-color: {colors.primary};
}}

QComboBox QAbstractItemView {{
    background-color: {colors.surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    selection-background-color: {colors.surface_light};
    selection-color: {colors.text_primary};
    outline: none;
    padding: {SPACING.xs}px;
}}

QComboBox QAbstractItemView::item {{
    padding: {SPACING.sm}px {SPACING.md}px;
    border-radius: {RADIUS.xs}px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {colors.surface_light};
}}

/* =============================================================================
   CHECKBOXES & RADIO BUTTONS
   ============================================================================= */

QCheckBox {{
    spacing: {SPACING.sm}px;
    color: {colors.text_primary};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors.border};
    border-radius: {RADIUS.xs}px;
    background-color: {colors.surface};
}}

QCheckBox::indicator:hover {{
    border-color: {colors.primary};
}}

QCheckBox::indicator:checked {{
    background-color: {colors.primary};
    border-color: {colors.primary};
}}

QCheckBox::indicator:checked:hover {{
    background-color: {colors.primary_light};
    border-color: {colors.primary_light};
}}

QCheckBox::indicator:disabled {{
    background-color: {colors.surface_light};
    border-color: {colors.border_light};
}}

QRadioButton {{
    spacing: {SPACING.sm}px;
    color: {colors.text_primary};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors.border};
    border-radius: 9px;
    background-color: {colors.surface};
}}

QRadioButton::indicator:hover {{
    border-color: {colors.primary};
}}

QRadioButton::indicator:checked {{
    border-color: {colors.primary};
    border-width: 5px;
    background-color: {colors.surface};
}}

/* =============================================================================
   SCROLLBARS
   ============================================================================= */

QScrollBar:vertical {{
    background-color: transparent;
    width: 12px;
    margin: 0;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors.surface_lighter};
    border-radius: 4px;
    min-height: 32px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors.text_disabled};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {colors.text_secondary};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 12px;
    margin: 0;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors.surface_lighter};
    border-radius: 4px;
    min-width: 32px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors.text_disabled};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* =============================================================================
   TAB WIDGET
   ============================================================================= */

QTabWidget::pane {{
    border: 1px solid {colors.border};
    border-top: none;
    background-color: {colors.surface};
    border-radius: 0 0 {RADIUS.md}px {RADIUS.md}px;
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors.text_secondary};
    padding: {SPACING.md}px {SPACING.xl}px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: {TYPOGRAPHY.weight_medium};
    font-size: {TYPOGRAPHY.text_sm}px;
    margin-right: {SPACING.xs}px;
}}

QTabBar::tab:hover {{
    color: {colors.text_primary};
    background-color: {colors.surface_light};
}}

QTabBar::tab:selected {{
    color: {colors.primary};
    border-bottom-color: {colors.primary};
}}

QTabBar::tab:disabled {{
    color: {colors.text_disabled};
}}

/* =============================================================================
   PROGRESS BAR
   ============================================================================= */

QProgressBar {{
    background-color: {colors.surface_light};
    border: none;
    border-radius: {RADIUS.xs}px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors.primary};
    border-radius: {RADIUS.xs}px;
}}

/* =============================================================================
   SLIDER
   ============================================================================= */

QSlider::groove:horizontal {{
    background-color: {colors.surface_lighter};
    height: 6px;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background-color: {colors.primary};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {colors.primary};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid {colors.surface};
}}

QSlider::handle:horizontal:hover {{
    background-color: {colors.primary_light};
    transform: scale(1.1);
}}

QSlider::handle:horizontal:pressed {{
    background-color: {colors.primary_dark};
}}

/* =============================================================================
   TABLE
   ============================================================================= */

QTableView,
QTableWidget {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    gridline-color: {colors.border_light};
    selection-background-color: rgba({_hex_to_rgb(colors.primary)}, 0.1);
}}

QTableView::item {{
    padding: {SPACING.sm}px {SPACING.md}px;
    border-bottom: 1px solid {colors.border_light};
}}

QTableView::item:selected {{
    background-color: rgba({_hex_to_rgb(colors.primary)}, 0.1);
    color: {colors.text_primary};
}}

QTableView::item:hover {{
    background-color: {colors.surface_light};
}}

QHeaderView::section {{
    background-color: {colors.surface_light};
    color: {colors.text_secondary};
    font-weight: {TYPOGRAPHY.weight_medium};
    font-size: {TYPOGRAPHY.text_sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    border: none;
    border-bottom: 1px solid {colors.border};
}}

QHeaderView::section:hover {{
    background-color: {colors.surface_lighter};
    color: {colors.text_primary};
}}

/* =============================================================================
   TREE VIEW
   ============================================================================= */

QTreeView {{
    background-color: {colors.surface};
    border: none;
    outline: none;
}}

QTreeView::item {{
    padding: {SPACING.sm}px {SPACING.sm}px;
    border-radius: {RADIUS.sm}px;
    margin: 1px 0;
}}

QTreeView::item:hover {{
    background-color: {colors.surface_light};
}}

QTreeView::item:selected {{
    background-color: rgba({_hex_to_rgb(colors.primary)}, 0.1);
    color: {colors.text_primary};
}}

QTreeView::branch {{
    background: transparent;
}}

/* =============================================================================
   LIST VIEW
   ============================================================================= */

QListView,
QListWidget {{
    background-color: {colors.surface};
    border: none;
    outline: none;
}}

QListView::item {{
    padding: {SPACING.sm}px {SPACING.md}px;
    border-radius: {RADIUS.sm}px;
    margin: 1px 0;
}}

QListView::item:hover {{
    background-color: {colors.surface_light};
}}

QListView::item:selected {{
    background-color: rgba({_hex_to_rgb(colors.primary)}, 0.1);
    color: {colors.text_primary};
}}

/* =============================================================================
   MENU BAR & MENUS
   ============================================================================= */

QMenuBar {{
    background-color: {colors.surface};
    border-bottom: 1px solid {colors.border};
    padding: 0 {SPACING.sm}px;
    spacing: 0;
}}

QMenuBar::item {{
    padding: {SPACING.sm}px {SPACING.md}px;
    color: {colors.text_secondary};
    border-radius: {RADIUS.sm}px;
    margin: {SPACING.xs}px 2px;
}}

QMenuBar::item:selected {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
}}

QMenuBar::item:pressed {{
    background-color: {colors.surface_lighter};
}}

QMenu {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px;
}}

QMenu::item {{
    padding: {SPACING.sm}px {SPACING.lg}px;
    color: {colors.text_primary};
    border-radius: {RADIUS.sm}px;
    margin: 1px 0;
}}

QMenu::item:selected {{
    background-color: {colors.surface_light};
}}

QMenu::item:disabled {{
    color: {colors.text_disabled};
}}

QMenu::separator {{
    height: 1px;
    background-color: {colors.border};
    margin: {SPACING.sm}px {SPACING.sm}px;
}}

QMenu::icon {{
    padding-left: {SPACING.sm}px;
}}

/* =============================================================================
   TOOLTIP
   ============================================================================= */

QToolTip {{
    background-color: {colors.text_primary};
    color: {colors.surface};
    border: none;
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    font-size: {TYPOGRAPHY.text_sm}px;
}}

/* =============================================================================
   GROUP BOX
   ============================================================================= */

QGroupBox {{
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    margin-top: 20px;
    padding-top: {SPACING.lg}px;
    font-weight: {TYPOGRAPHY.weight_medium};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {SPACING.md}px;
    padding: 0 {SPACING.sm}px;
    color: {colors.text_primary};
    background-color: {colors.background};
}}

/* =============================================================================
   SPLITTER
   ============================================================================= */

QSplitter::handle {{
    background-color: {colors.border};
}}

QSplitter::handle:hover {{
    background-color: {colors.primary};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* =============================================================================
   STATUS BAR
   ============================================================================= */

QStatusBar {{
    background-color: {colors.surface};
    color: {colors.text_secondary};
    font-size: {TYPOGRAPHY.text_sm}px;
    border-top: 1px solid {colors.border};
    padding: 0 {SPACING.md}px;
    min-height: {LAYOUT.statusbar_height}px;
}}

QStatusBar::item {{
    border: none;
}}

/* =============================================================================
   TOOLBAR
   ============================================================================= */

QToolBar {{
    background-color: {colors.surface};
    border-bottom: 1px solid {colors.border};
    padding: {SPACING.xs}px {SPACING.md}px;
    spacing: {SPACING.xs}px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {colors.border};
    margin: {SPACING.xs}px {SPACING.sm}px;
}}

QToolButton {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px;
    min-width: 32px;
    min-height: 32px;
}}

QToolButton:hover {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
}}

QToolButton:pressed {{
    background-color: {colors.surface_lighter};
}}

QToolButton:checked {{
    background-color: rgba({_hex_to_rgb(colors.primary)}, 0.1);
    color: {colors.primary};
}}

/* =============================================================================
   DOCK WIDGET
   ============================================================================= */

QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {colors.surface_light};
    padding: {SPACING.sm}px {SPACING.md}px;
    border-bottom: 1px solid {colors.border};
    font-weight: {TYPOGRAPHY.weight_medium};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

/* =============================================================================
   DIALOG
   ============================================================================= */

QDialog {{
    background-color: {colors.surface};
}}

QDialogButtonBox {{
    button-layout: 3;
}}

/* =============================================================================
   SPIN BOX
   ============================================================================= */

QSpinBox,
QDoubleSpinBox {{
    padding-right: 20px;
}}

QSpinBox::up-button,
QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border: none;
    border-left: 1px solid {colors.border};
    border-top-right-radius: {RADIUS.sm}px;
}}

QSpinBox::down-button,
QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border: none;
    border-left: 1px solid {colors.border};
    border-bottom-right-radius: {RADIUS.sm}px;
}}

QSpinBox::up-button:hover,
QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::down-button:hover {{
    background-color: {colors.surface_light};
}}

QSpinBox::up-arrow,
QDoubleSpinBox::up-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {colors.text_secondary};
    width: 0;
    height: 0;
}}

QSpinBox::down-arrow,
QDoubleSpinBox::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {colors.text_secondary};
    width: 0;
    height: 0;
}}

/* =============================================================================
   CALENDAR
   ============================================================================= */

QCalendarWidget {{
    background-color: {colors.surface};
}}

QCalendarWidget QToolButton {{
    color: {colors.text_primary};
    font-size: {TYPOGRAPHY.text_base}px;
    font-weight: {TYPOGRAPHY.weight_medium};
}}

QCalendarWidget QSpinBox {{
    font-size: {TYPOGRAPHY.text_base}px;
}}

QCalendarWidget QTableView {{
    selection-background-color: {colors.primary};
    selection-color: {colors.primary_foreground};
}}
"""


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB values string for rgba()."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


def _blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors together."""
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')

    r = int(int(c1[0:2], 16) * (1 - ratio) + int(c2[0:2], 16) * ratio)
    g = int(int(c1[2:4], 16) * (1 - ratio) + int(c2[2:4], 16) * ratio)
    b = int(int(c1[4:6], 16) * (1 - ratio) + int(c2[4:6], 16) * ratio)

    return f"#{r:02x}{g:02x}{b:02x}"


def _adjust_color(hex_color: str, amount: int) -> str:
    """Lighten (positive) or darken (negative) a hex color."""
    hex_color = hex_color.lstrip('#')
    r = max(0, min(255, int(hex_color[0:2], 16) + amount))
    g = max(0, min(255, int(hex_color[2:4], 16) + amount))
    b = max(0, min(255, int(hex_color[4:6], 16) + amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _adjust_alpha(hex_color: str, alpha: float) -> str:
    """Convert hex color to rgba with specified alpha."""
    rgb = _hex_to_rgb(hex_color)
    return f"rgba({rgb}, {alpha})"
