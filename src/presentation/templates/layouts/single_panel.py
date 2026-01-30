"""
Single Panel Layout

A simple full-width content layout with optional padding.

┌─────────────────────────────────────────┐
│                                         │
│            FULL WIDTH CONTENT           │
│                                         │
└─────────────────────────────────────────┘

Good for settings pages, reports, charts, etc.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_theme


class SinglePanelLayout(QWidget):
    """
    Simple full-width content layout.

    Can optionally include:
    - Padding around content
    - Scrollable container
    - Maximum content width (centered)

    Usage:
        layout = SinglePanelLayout(colors=colors, scrollable=True)
        layout.set_content(my_form)
    """

    def __init__(
        self,
        padding: int = 0,
        scrollable: bool = False,
        max_width: int = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._padding = padding
        self._scrollable = scrollable
        self._max_width = max_width

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

        if self._scrollable:
            # Scrollable container
            self._scroll = QScrollArea()
            self._scroll.setWidgetResizable(True)
            self._scroll.setFrameShape(QFrame.Shape.NoFrame)
            self._scroll.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {self._colors.background};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {self._colors.surface};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {self._colors.surface_light};
                    border-radius: 5px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {self._colors.primary};
                }}
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)

            # Inner content widget
            self._content_container = QWidget()
            self._content_layout = QVBoxLayout(self._content_container)
            self._content_layout.setContentsMargins(
                self._padding, self._padding, self._padding, self._padding
            )
            self._content_layout.setSpacing(0)

            if self._max_width:
                # Center content with max width
                self._content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            self._scroll.setWidget(self._content_container)
            layout.addWidget(self._scroll)
        else:
            # Non-scrollable
            self._content_container = QWidget()
            self._content_layout = QVBoxLayout(self._content_container)
            self._content_layout.setContentsMargins(
                self._padding, self._padding, self._padding, self._padding
            )
            self._content_layout.setSpacing(0)

            if self._max_width:
                self._content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            layout.addWidget(self._content_container)

    def set_content(self, widget: QWidget):
        """Set the content widget"""
        self._clear_layout(self._content_layout)

        if self._max_width:
            widget.setMaximumWidth(self._max_width)

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._content_layout.addWidget(widget)

    def _clear_layout(self, layout: QVBoxLayout):
        """Remove all widgets from a layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    @property
    def content_container(self) -> QWidget:
        """Access content container"""
        return self._content_container
