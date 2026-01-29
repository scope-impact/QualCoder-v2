"""
Stylesheet generator for PyQt6
Converts Material Design tokens to QSS (Qt Style Sheets)
Based on mockups/css/material-theme.css
"""

from .tokens import ColorPalette, SPACING, RADIUS, TYPOGRAPHY, LAYOUT


def generate_stylesheet(colors: ColorPalette) -> str:
    """Generate complete QSS stylesheet from design tokens"""

    return f"""
/* ===== Base ===== */
QWidget {{
    font-family: {TYPOGRAPHY.font_family};
    font-size: {TYPOGRAPHY.text_base}px;
    color: {colors.text_primary};
    background-color: transparent;
}}

QMainWindow, QDialog {{
    background-color: {colors.background};
}}

/* ===== Buttons ===== */
QPushButton {{
    background-color: {colors.primary};
    color: {colors.primary_foreground};
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px {SPACING.xl}px;
    font-size: {TYPOGRAPHY.text_base}px;
    font-weight: {TYPOGRAPHY.weight_medium};
    min-height: 36px;
}}

QPushButton:hover {{
    background-color: {colors.primary_light};
}}

QPushButton:pressed {{
    background-color: {colors.primary_dark};
}}

QPushButton:disabled {{
    background-color: {colors.surface_lighter};
    color: {colors.text_disabled};
}}

QPushButton:focus {{
    outline: none;
    border: 2px solid {colors.ring};
}}

/* Secondary Button */
QPushButton[variant="secondary"] {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
    border: none;
}}

QPushButton[variant="secondary"]:hover {{
    background-color: {colors.surface_lighter};
}}

/* Outline Button */
QPushButton[variant="outline"] {{
    background-color: transparent;
    color: {colors.text_primary};
    border: 1px solid {colors.border};
}}

QPushButton[variant="outline"]:hover {{
    background-color: {colors.surface_light};
    border-color: {colors.primary};
}}

/* Ghost Button */
QPushButton[variant="ghost"] {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
}}

QPushButton[variant="ghost"]:hover {{
    background-color: {colors.surface_light};
    color: {colors.primary};
}}

/* Destructive Button */
QPushButton[variant="destructive"], QPushButton[variant="danger"] {{
    background-color: {colors.error};
    color: {colors.error_foreground};
}}

QPushButton[variant="destructive"]:hover, QPushButton[variant="danger"]:hover {{
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

/* Icon Button */
QPushButton[variant="icon"] {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px;
    min-width: 36px;
    min-height: 36px;
}}

QPushButton[variant="icon"]:hover {{
    background-color: {colors.surface_light};
    color: {colors.primary};
}}

/* ===== Input Fields ===== */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    font-size: {TYPOGRAPHY.text_base}px;
    selection-background-color: {colors.primary};
    selection-color: {colors.primary_foreground};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors.primary};
    background-color: {colors.surface_light};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {colors.surface_lighter};
    color: {colors.text_disabled};
}}

QLineEdit[error="true"] {{
    border-color: {colors.error};
}}

/* Placeholder text */
QLineEdit::placeholder {{
    color: {colors.text_disabled};
}}

/* ===== Labels ===== */
QLabel {{
    color: {colors.text_primary};
    background-color: transparent;
}}

QLabel[variant="muted"], QLabel[variant="secondary"] {{
    color: {colors.text_secondary};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

QLabel[variant="title"] {{
    font-size: {TYPOGRAPHY.text_xl}px;
    font-weight: {TYPOGRAPHY.weight_medium};
}}

QLabel[variant="description"], QLabel[variant="hint"] {{
    color: {colors.text_hint};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

QLabel[variant="error"] {{
    color: {colors.error};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

/* ===== Cards (QFrame) ===== */
QFrame[variant="card"] {{
    background-color: {colors.surface};
    border: none;
    border-radius: {RADIUS.lg}px;
}}

QFrame[variant="panel"] {{
    background-color: {colors.surface};
    border-right: 1px solid {colors.border};
}}

/* ===== Combo Box ===== */
QComboBox {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    padding-right: {SPACING.xxl}px;
    font-size: {TYPOGRAPHY.text_sm}px;
    min-height: 32px;
}}

QComboBox:hover {{
    border-color: {colors.primary};
}}

QComboBox:focus {{
    border-color: {colors.primary};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors.text_secondary};
    margin-right: 8px;
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

/* ===== Check Box ===== */
QCheckBox {{
    spacing: {SPACING.sm}px;
    color: {colors.text_primary};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors.text_disabled};
    border-radius: {RADIUS.xs}px;
    background-color: transparent;
}}

QCheckBox::indicator:hover {{
    border-color: {colors.primary};
}}

QCheckBox::indicator:checked {{
    background-color: {colors.primary};
    border-color: {colors.primary};
}}

/* ===== Radio Button ===== */
QRadioButton {{
    spacing: {SPACING.sm}px;
    color: {colors.text_primary};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors.text_disabled};
    border-radius: 9px;
    background-color: transparent;
}}

QRadioButton::indicator:hover {{
    border-color: {colors.primary};
}}

QRadioButton::indicator:checked {{
    border-color: {colors.primary};
    background-color: {colors.primary};
}}

/* ===== Scroll Bar ===== */
QScrollBar:vertical {{
    background-color: {colors.surface};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {colors.surface_lighter};
    border-radius: 4px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors.text_disabled};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {colors.surface};
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors.surface_lighter};
    border-radius: 4px;
    min-width: 40px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors.text_disabled};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    border: 1px solid {colors.border};
    border-top: none;
    background-color: {colors.surface};
}}

QTabBar {{
    background-color: {colors.surface};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors.text_secondary};
    padding: {SPACING.md}px {SPACING.xxl}px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: {TYPOGRAPHY.weight_medium};
    font-size: {TYPOGRAPHY.text_sm}px;
}}

QTabBar::tab:hover {{
    color: {colors.text_primary};
    background-color: {colors.surface_light};
}}

QTabBar::tab:selected {{
    color: {colors.primary};
    border-bottom-color: {colors.primary};
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    background-color: {colors.surface_light};
    border: none;
    border-radius: 2px;
    height: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors.primary};
    border-radius: 2px;
}}

/* ===== Slider ===== */
QSlider::groove:horizontal {{
    background-color: {colors.surface_light};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {colors.primary};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {colors.primary_light};
}}

/* ===== Table ===== */
QTableView, QTableWidget {{
    background-color: {colors.surface};
    border: none;
    gridline-color: {colors.border};
    selection-background-color: rgba(0, 150, 136, 0.1);
}}

QTableView::item {{
    padding: {SPACING.md}px {SPACING.lg}px;
    border-bottom: 1px solid {colors.border};
}}

QTableView::item:selected {{
    background-color: rgba(0, 150, 136, 0.1);
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
    padding: {SPACING.md}px {SPACING.lg}px;
    border: none;
    border-bottom: 1px solid {colors.border};
    text-transform: uppercase;
}}

/* ===== Tree View ===== */
QTreeView {{
    background-color: {colors.surface};
    border: none;
    outline: none;
}}

QTreeView::item {{
    padding: {SPACING.sm}px;
    border-radius: {RADIUS.sm}px;
}}

QTreeView::item:hover {{
    background-color: {colors.surface_light};
}}

QTreeView::item:selected {{
    background-color: rgba(0, 150, 136, 0.1);
    color: {colors.text_primary};
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    border-image: none;
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    border-image: none;
}}

/* ===== List View ===== */
QListView, QListWidget {{
    background-color: {colors.surface};
    border: none;
    outline: none;
}}

QListView::item {{
    padding: {SPACING.sm}px {SPACING.md}px;
    border-radius: {RADIUS.sm}px;
}}

QListView::item:hover {{
    background-color: {colors.surface_light};
}}

QListView::item:selected {{
    background-color: rgba(0, 150, 136, 0.1);
    color: {colors.text_primary};
}}

/* ===== Menu ===== */
QMenuBar {{
    background-color: {colors.surface};
    border-bottom: 1px solid {colors.border};
    padding: 0 {SPACING.sm}px;
}}

QMenuBar::item {{
    padding: {SPACING.sm}px {SPACING.lg}px;
    color: {colors.text_secondary};
    border-radius: {RADIUS.xs}px;
    margin: 2px;
}}

QMenuBar::item:selected {{
    background-color: {colors.surface_light};
    color: {colors.text_primary};
}}

QMenu {{
    background-color: {colors.surface};
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px 0;
}}

QMenu::item {{
    padding: {SPACING.sm}px {SPACING.lg}px;
    color: {colors.text_primary};
}}

QMenu::item:selected {{
    background-color: {colors.surface_light};
}}

QMenu::separator {{
    height: 1px;
    background-color: {colors.border};
    margin: {SPACING.sm}px 0;
}}

/* ===== Tooltip ===== */
QToolTip {{
    background-color: {colors.surface_elevated};
    color: {colors.text_primary};
    border: none;
    border-radius: {RADIUS.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    font-size: {TYPOGRAPHY.text_sm}px;
}}

/* ===== Group Box ===== */
QGroupBox {{
    border: 1px solid {colors.border};
    border-radius: {RADIUS.md}px;
    margin-top: 16px;
    padding-top: {SPACING.lg}px;
    font-weight: {TYPOGRAPHY.weight_medium};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {SPACING.md}px;
    padding: 0 {SPACING.xs}px;
    color: {colors.text_primary};
    background-color: {colors.background};
}}

/* ===== Splitter ===== */
QSplitter::handle {{
    background-color: {colors.border};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {colors.primary_dark};
    color: white;
    font-size: {TYPOGRAPHY.text_sm}px;
    padding: 0 {SPACING.lg}px;
    min-height: {LAYOUT.statusbar_height}px;
}}

QStatusBar::item {{
    border: none;
}}

/* ===== Tool Bar ===== */
QToolBar {{
    background-color: {colors.surface};
    border-bottom: 1px solid {colors.border};
    padding: {SPACING.sm}px {SPACING.lg}px;
    spacing: {SPACING.sm}px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {colors.border};
    margin: 0 {SPACING.sm}px;
}}

QToolButton {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    min-width: 36px;
    min-height: 36px;
}}

QToolButton:hover {{
    background-color: {colors.surface_light};
    color: {colors.primary};
}}

QToolButton:pressed {{
    background-color: {colors.surface_lighter};
}}

QToolButton:checked {{
    background-color: {colors.primary};
    color: white;
}}

/* ===== Dock Widget ===== */
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

/* ===== Dialog Button Box ===== */
QDialogButtonBox {{
    button-layout: 3;
}}
"""


def _adjust_color(hex_color: str, amount: int) -> str:
    """Lighten (positive) or darken (negative) a hex color"""
    hex_color = hex_color.lstrip('#')
    r = max(0, min(255, int(hex_color[0:2], 16) + amount))
    g = max(0, min(255, int(hex_color[2:4], 16) + amount))
    b = max(0, min(255, int(hex_color[4:6], 16) + amount))
    return f"#{r:02x}{g:02x}{b:02x}"
