"""
Details Panel Organism

A panel showing contextual details for the coding interface:
- Selected code information
- Overlapping codes warning
- File memo
- AI Assistant actions
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    Button,
    CodeDetailCard,
    ColorPalette,
    Icon,
    InfoCard,
    ProgressBar,
    get_theme,
)


class DetailsPanel(QFrame):
    """
    Panel showing selected code details, overlaps, and file memo.

    Signals:
        ai_chat_clicked: Emitted when AI chat button is clicked
        ai_suggest_clicked: Emitted when suggest codes button is clicked
    """

    ai_chat_clicked = pyqtSignal()
    ai_suggest_clicked = pyqtSignal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the details panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            DetailsPanel {{
                background-color: {self._colors.surface};
                border-left: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Selected Code card
        self._code_card = InfoCard(
            title="Selected Code",
            icon="mdi6.information",
            colors=self._colors,
        )
        self._code_detail = CodeDetailCard(
            color="#808080",
            name="No code selected",
            memo="Select a code from the tree to see details.",
            colors=self._colors,
        )
        self._code_card.set_content(self._code_detail)
        container_layout.addWidget(self._code_card)

        # Overlapping Codes card
        self._overlap_card = InfoCard(
            title="Overlapping Codes",
            icon="mdi6.alert",
            colors=self._colors,
        )
        self._overlap_content = self._create_overlap_content([])
        self._overlap_card.set_content(self._overlap_content)
        container_layout.addWidget(self._overlap_card)

        # File Memo card
        self._memo_card = InfoCard(
            title="File Memo",
            icon="mdi6.bookmark",
            colors=self._colors,
        )
        self._memo_content = self._create_memo_content("", 0)
        self._memo_card.set_content(self._memo_content)
        container_layout.addWidget(self._memo_card)

        # AI Assistant card
        self._ai_card = InfoCard(
            title="AI Assistant",
            icon="mdi6.robot",
            colors=self._colors,
        )
        ai_content = self._create_ai_content()
        self._ai_card.set_content(ai_content)
        container_layout.addWidget(self._ai_card)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_overlap_content(self, segments: list[tuple[str, list[str]]]) -> QWidget:
        """
        Create the overlapping codes content.

        Args:
            segments: List of (segment_text, [color1, color2, ...]) tuples
        """
        widget = QFrame()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        if not segments:
            # No overlaps message
            label = QLabel("No overlapping codes detected")
            label.setStyleSheet(
                f"color: {self._colors.text_disabled}; font-size: {TYPOGRAPHY.text_xs}px;"
            )
            layout.addWidget(label)
            return widget

        # Warning indicator
        warning = QFrame()
        warning.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 152, 0, 0.1);
                border: 1px solid rgba(255, 152, 0, 0.3);
                border-radius: {RADIUS.md}px;
            }}
        """)
        warning_layout = QHBoxLayout(warning)
        warning_layout.setContentsMargins(
            SPACING.md, SPACING.sm, SPACING.md, SPACING.sm
        )
        warning_layout.setSpacing(SPACING.sm)

        icon = Icon("mdi6.information", size=16, color="#FF9800", colors=self._colors)
        warning_layout.addWidget(icon)

        label = QLabel(f"{len(segments)} segments have multiple codes")
        label.setStyleSheet(
            f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;"
        )
        warning_layout.addWidget(label)
        warning_layout.addStretch()

        layout.addWidget(warning)

        # Segment details
        for i, (_, colors) in enumerate(segments):
            seg = QFrame()
            seg.setStyleSheet(f"""
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
            """)
            seg_layout = QVBoxLayout(seg)
            seg_layout.setContentsMargins(
                SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm
            )
            seg_layout.setSpacing(SPACING.xs)

            title = QLabel(f"Segment {i + 1}:")
            title.setStyleSheet(
                f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_xs}px; font-weight: bold;"
            )
            seg_layout.addWidget(title)

            dots = QHBoxLayout()
            dots.setSpacing(SPACING.xs)
            for c in colors:
                dot = QFrame()
                dot.setFixedSize(12, 12)
                dot.setStyleSheet(f"background-color: {c}; border-radius: 2px;")
                dots.addWidget(dot)
            dots.addStretch()
            seg_layout.addLayout(dots)

            layout.addWidget(seg)

        return widget

    def _create_memo_content(self, memo_text: str, progress: int) -> QWidget:
        """
        Create the file memo content.

        Args:
            memo_text: The memo text
            progress: Coding progress percentage (0-100)
        """
        widget = QFrame()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        if memo_text:
            memo_label = QLabel(memo_text)
            memo_label.setWordWrap(True)
            memo_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
                line-height: 1.6;
            """)
            layout.addWidget(memo_label)
        else:
            no_memo = QLabel("No memo for this file")
            no_memo.setStyleSheet(
                f"color: {self._colors.text_disabled}; font-size: {TYPOGRAPHY.text_xs}px;"
            )
            layout.addWidget(no_memo)

        # Progress bar
        if progress > 0:
            progress_bar = ProgressBar(value=progress, colors=self._colors)
            layout.addWidget(progress_bar)

            progress_label = QLabel(f"Coding progress: {progress}%")
            progress_label.setStyleSheet(
                f"color: {self._colors.text_disabled}; font-size: {TYPOGRAPHY.text_xs}px;"
            )
            layout.addWidget(progress_label)

        return widget

    def _create_ai_content(self) -> QWidget:
        """Create the AI assistant content."""
        widget = QFrame()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        chat_btn = Button("Start AI Chat", variant="primary", colors=self._colors)
        chat_btn.clicked.connect(self.ai_chat_clicked.emit)
        layout.addWidget(chat_btn)

        suggest_btn = Button("Suggest Codes", variant="secondary", colors=self._colors)
        suggest_btn.clicked.connect(self.ai_suggest_clicked.emit)
        layout.addWidget(suggest_btn)

        return widget

    def set_selected_code(self, color: str, name: str, memo: str, example: str = None):
        """
        Update the selected code display.

        Args:
            color: Code color hex string
            name: Code name
            memo: Code memo/description
            example: Optional example text
        """
        # Remove old detail card and create new one
        old_detail = self._code_detail
        self._code_detail = CodeDetailCard(
            color=color,
            name=name,
            memo=memo,
            example=example,
            colors=self._colors,
        )
        self._code_card.set_content(self._code_detail)
        old_detail.deleteLater()

    def set_overlapping_codes(self, segments: list[tuple[str, list[str]]]):
        """
        Update the overlapping codes display.

        Args:
            segments: List of (segment_text, [color1, color2, ...]) tuples
        """
        old_content = self._overlap_content
        self._overlap_content = self._create_overlap_content(segments)
        self._overlap_card.set_content(self._overlap_content)
        old_content.deleteLater()

    def set_file_memo(self, memo_text: str, progress: int = 0):
        """
        Update the file memo display.

        Args:
            memo_text: The memo text
            progress: Coding progress percentage (0-100)
        """
        old_content = self._memo_content
        self._memo_content = self._create_memo_content(memo_text, progress)
        self._memo_card.set_content(self._memo_content)
        old_content.deleteLater()
