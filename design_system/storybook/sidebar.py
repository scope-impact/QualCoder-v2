"""
StorybookSidebar component for navigation
"""

from typing import Callable

from ..qt_compat import (
    QFrame, QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, Qt,
)

from ..tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class StorybookSidebar(QFrame):
    """Sidebar navigation for storybook"""

    def __init__(self, on_select: Callable, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme()
        self._on_select = on_select
        self._buttons = {}
        self._active = None

        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.background};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.background};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)

        title = QLabel("Design System")
        title.setStyleSheet(f"""
            color: {self._colors.primary};
            font-size: 18px;
            font-weight: bold;
        """)
        header_layout.addWidget(title)

        subtitle = QLabel("Component Storybook")
        subtitle.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Navigation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        nav_container = QWidget()
        self._nav_layout = QVBoxLayout(nav_container)
        self._nav_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._nav_layout.setSpacing(SPACING.xs)
        self._nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(nav_container)
        layout.addWidget(scroll, 1)

    def add_section(self, title: str):
        label = QLabel(title.upper())
        label.setStyleSheet(f"""
            color: {self._colors.primary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: {SPACING.lg}px {SPACING.sm}px {SPACING.xs}px;
            margin-top: {SPACING.sm}px;
        """)
        self._nav_layout.addWidget(label)

    def add_item(self, key: str, label: str):
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._select(key))
        self._buttons[key] = btn
        self._nav_layout.addWidget(btn)
        self._style_button(btn, False)

        if self._active is None:
            self._select(key)

    def _select(self, key: str):
        self._active = key
        for k, btn in self._buttons.items():
            self._style_button(btn, k == key)
        self._on_select(key)

    def _style_button(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary}26;
                    color: {self._colors.primary};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {SPACING.sm}px {SPACING.md}px;
                    text-align: left;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_primary};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {SPACING.sm}px {SPACING.md}px;
                    text-align: left;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)
