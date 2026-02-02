"""
Project Screen

Landing screen for project management - open existing or create new projects.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from design_system import SPACING, TYPOGRAPHY, Button, ColorPalette


class ProjectScreen:
    """Project management screen with Open/Create buttons."""

    def __init__(self, colors: ColorPalette, on_open=None, on_create=None):
        self._colors = colors
        self._on_open = on_open
        self._on_create = on_create

    def get_toolbar_content(self):
        return None

    def get_content(self):
        container = QWidget()
        container.setStyleSheet(f"background-color: {self._colors.background};")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.lg)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("QualCoder")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_4xl}px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Qualitative Data Analysis")
        subtitle.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_lg}px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(SPACING.xl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING.md)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        open_btn = Button(
            "Open Project", variant="secondary", size="lg", colors=self._colors
        )
        if self._on_open:
            open_btn.clicked.connect(self._on_open)
        btn_layout.addWidget(open_btn)

        create_btn = Button(
            "Create Project", variant="primary", size="lg", colors=self._colors
        )
        if self._on_create:
            create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        return container

    def get_status_message(self):
        return "Welcome to QualCoder"
