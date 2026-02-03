"""
AI Suggestion Card Molecule

A card that displays a single AI-suggested code with approve/reject actions.

Pure presentation component - emits signals for approve/reject,
receives suggestion data to display.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    Button,
    Card,
    ColorPalette,
    Icon,
    get_colors,
)


class AISuggestionCard(Card):
    """
    Single AI code suggestion for display in the details panel.

    Displays:
    - Code color swatch and name
    - Confidence indicator
    - Rationale text
    - Context preview
    - Approve/Reject actions

    Signals:
        approved(str): Emitted when approve is clicked, with suggestion_id
        rejected(str): Emitted when reject is clicked, with suggestion_id
        details_clicked(str): Emitted when card is clicked for details

    Example:
        card = AISuggestionCard(
            suggestion_id="abc123",
            name="Theme: Learning",
            color="#4CAF50",
            rationale="Text discusses learning enthusiasm...",
            confidence=0.85,
            context_preview="I really like learning new things...",
        )
        card.approved.connect(lambda sid: print(f"Approved: {sid}"))
    """

    approved = Signal(str)
    rejected = Signal(str)
    details_clicked = Signal(str)

    def __init__(
        self,
        suggestion_id: str,
        name: str,
        color: str,
        rationale: str,
        confidence: float,
        context_preview: str = "",
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the suggestion card.

        Args:
            suggestion_id: Unique identifier for the suggestion
            name: Suggested code name
            color: Suggested code color (hex string)
            rationale: AI's reasoning for this suggestion
            confidence: Confidence score (0.0-1.0)
            context_preview: Preview of text context
            colors: Color palette for styling
            parent: Parent widget
        """
        self._colors = colors or get_colors()
        super().__init__(colors=self._colors, parent=parent, shadow=False, elevation=1)
        self._suggestion_id = suggestion_id
        self._name = name
        self._code_color = color
        self._rationale = rationale
        self._confidence = confidence
        self._context_preview = context_preview

        self._setup_ui()

    def _setup_ui(self):
        """Build the card UI."""
        # Set hover style
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            AISuggestionCard:hover {{
                background-color: {self._colors.surface_light};
                border-color: {self._colors.primary};
            }}
        """
        )

        self._layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        self._layout.setSpacing(SPACING.sm)

        # Header: color swatch + name + confidence
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        # Color swatch
        from PySide6.QtWidgets import QFrame

        swatch = QFrame()
        swatch.setFixedSize(16, 16)
        swatch.setStyleSheet(
            f"background-color: {self._code_color}; border-radius: {RADIUS.sm}px;"
        )
        header.addWidget(swatch)

        # Name
        name_label = QLabel(self._name)
        name_label.setStyleSheet(
            f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """
        )
        header.addWidget(name_label, 1)

        # Confidence badge
        confidence_pct = int(self._confidence * 100)
        badge_color = (
            self._colors.success
            if self._confidence >= 0.7
            else (
                self._colors.warning if self._confidence >= 0.5 else self._colors.error
            )
        )
        confidence_label = QLabel(f"{confidence_pct}%")
        confidence_label.setStyleSheet(
            f"""
            color: {badge_color};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_bold};
            background-color: {badge_color}20;
            padding: 2px 6px;
            border-radius: {RADIUS.sm}px;
        """
        )
        header.addWidget(confidence_label)

        self._layout.addLayout(header)

        # Rationale
        rationale_label = QLabel(self._rationale)
        rationale_label.setWordWrap(True)
        rationale_label.setStyleSheet(
            f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            line-height: 1.4;
        """
        )
        self._layout.addWidget(rationale_label)

        # Context preview (if any)
        if self._context_preview:
            context_frame = QFrame()
            context_frame.setStyleSheet(
                f"""
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
                border-left: 3px solid {self._code_color};
            """
            )
            context_layout = QVBoxLayout(context_frame)
            context_layout.setContentsMargins(
                SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs
            )

            preview_text = (
                self._context_preview[:100] + "..."
                if len(self._context_preview) > 100
                else self._context_preview
            )
            context_label = QLabel(f'"{preview_text}"')
            context_label.setWordWrap(True)
            context_label.setStyleSheet(
                f"""
                color: {self._colors.text_disabled};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-style: italic;
            """
            )
            context_layout.addWidget(context_label)
            self._layout.addWidget(context_frame)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(SPACING.sm)

        approve_btn = Button(
            "Approve",
            variant="primary",
            size="small",
            colors=self._colors,
        )
        approve_btn.clicked.connect(self._on_approve)
        actions.addWidget(approve_btn)

        reject_btn = Button(
            "Reject",
            variant="ghost",
            size="small",
            colors=self._colors,
        )
        reject_btn.clicked.connect(self._on_reject)
        actions.addWidget(reject_btn)

        actions.addStretch()
        self._layout.addLayout(actions)

    def _on_approve(self):
        """Handle approve click."""
        self.approved.emit(self._suggestion_id)

    def _on_reject(self):
        """Handle reject click."""
        self.rejected.emit(self._suggestion_id)

    def mousePressEvent(self, event):
        """Handle click for details."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only emit details if not clicking a button
            child = self.childAt(event.pos())
            if not isinstance(child, Button):
                self.details_clicked.emit(self._suggestion_id)

    # =========================================================================
    # Public API
    # =========================================================================

    def get_suggestion_id(self) -> str:
        """Get the suggestion ID."""
        return self._suggestion_id

    def get_name(self) -> str:
        """Get the suggested code name."""
        return self._name

    def get_color(self) -> str:
        """Get the suggested code color."""
        return self._code_color

    def get_confidence(self) -> float:
        """Get the confidence score."""
        return self._confidence


class AISuggestionsPanel(Card):
    """
    Panel displaying multiple AI suggestions with loading/empty states.

    Signals:
        suggestion_approved(str): A suggestion was approved
        suggestion_rejected(str): A suggestion was rejected
        dismiss_all(): All suggestions dismissed
    """

    suggestion_approved = Signal(str)
    suggestion_rejected = Signal(str)
    dismiss_all = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the suggestions panel.

        Args:
            colors: Color palette for styling
            parent: Parent widget
        """
        self._colors = colors or get_colors()
        super().__init__(colors=self._colors, parent=parent, shadow=False, elevation=0)

        self._suggestions: list[AISuggestionCard] = []
        self._is_loading = False

        self._setup_ui()

    def _setup_ui(self):
        """Build the panel UI."""
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.sm)

        # Header
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        icon = Icon(
            "mdi6.lightbulb-on",
            size=16,
            color=self._colors.primary,
            colors=self._colors,
        )
        header.addWidget(icon)

        self._title = QLabel("AI Suggestions")
        self._title.setStyleSheet(
            f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """
        )
        header.addWidget(self._title, 1)

        self._dismiss_btn = Button(
            "Dismiss All",
            variant="ghost",
            size="small",
            colors=self._colors,
        )
        self._dismiss_btn.clicked.connect(self.dismiss_all.emit)
        self._dismiss_btn.setVisible(False)
        header.addWidget(self._dismiss_btn)

        self._layout.addLayout(header)

        # Content container
        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(SPACING.sm)
        self._layout.addLayout(self._content)

        # Default: empty state
        self._show_empty_state()

    def _clear_content(self):
        """Clear all content from the panel."""
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._suggestions.clear()

    def _show_empty_state(self):
        """Show empty state message."""
        self._clear_content()
        self._dismiss_btn.setVisible(False)

        label = QLabel("Click 'Suggest Codes' to get AI suggestions for selected text.")
        label.setWordWrap(True)
        label.setStyleSheet(
            f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_xs}px;
        """
        )
        self._content.addWidget(label)

    def _show_loading_state(self):
        """Show loading state."""
        self._clear_content()
        self._is_loading = True
        self._dismiss_btn.setVisible(False)

        loading_layout = QHBoxLayout()
        loading_layout.setSpacing(SPACING.sm)

        icon = Icon(
            "mdi6.loading",
            size=16,
            color=self._colors.primary,
            colors=self._colors,
        )
        loading_layout.addWidget(icon)

        label = QLabel("Analyzing text...")
        label.setStyleSheet(
            f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """
        )
        loading_layout.addWidget(label)
        loading_layout.addStretch()

        from PySide6.QtWidgets import QWidget

        container = QWidget()
        container.setLayout(loading_layout)
        self._content.addWidget(container)

    def set_suggestions(self, suggestions: list[dict]):
        """
        Set the suggestions to display.

        Args:
            suggestions: List of suggestion dicts with:
                - suggestion_id: str
                - name: str
                - color: str
                - rationale: str
                - confidence: float
                - context_preview: str (optional)
        """
        self._clear_content()
        self._is_loading = False

        if not suggestions:
            self._show_no_suggestions()
            return

        self._dismiss_btn.setVisible(True)
        self._title.setText(f"AI Suggestions ({len(suggestions)})")

        for data in suggestions:
            card = AISuggestionCard(
                suggestion_id=data["suggestion_id"],
                name=data["name"],
                color=data["color"],
                rationale=data["rationale"],
                confidence=data["confidence"],
                context_preview=data.get("context_preview", ""),
                colors=self._colors,
            )
            card.approved.connect(self.suggestion_approved.emit)
            card.rejected.connect(self.suggestion_rejected.emit)
            self._suggestions.append(card)
            self._content.addWidget(card)

    def _show_no_suggestions(self):
        """Show no suggestions message."""
        self._dismiss_btn.setVisible(False)
        self._title.setText("AI Suggestions")

        label = QLabel("No code suggestions found for this text.")
        label.setWordWrap(True)
        label.setStyleSheet(
            f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_xs}px;
        """
        )
        self._content.addWidget(label)

    def show_loading(self):
        """Start loading state."""
        self._show_loading_state()

    def show_error(self, message: str):
        """Show error message."""
        self._clear_content()
        self._is_loading = False
        self._dismiss_btn.setVisible(False)

        error_layout = QHBoxLayout()
        error_layout.setSpacing(SPACING.sm)

        icon = Icon(
            "mdi6.alert-circle",
            size=16,
            color=self._colors.error,
            colors=self._colors,
        )
        error_layout.addWidget(icon)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"""
            color: {self._colors.error};
            font-size: {TYPOGRAPHY.text_xs}px;
        """
        )
        error_layout.addWidget(label, 1)

        from PySide6.QtWidgets import QWidget

        container = QWidget()
        container.setLayout(error_layout)
        self._content.addWidget(container)

    def remove_suggestion(self, suggestion_id: str):
        """Remove a suggestion from the panel."""
        for card in self._suggestions:
            if card.get_suggestion_id() == suggestion_id:
                self._suggestions.remove(card)
                card.deleteLater()
                break

        # Update title
        if self._suggestions:
            self._title.setText(f"AI Suggestions ({len(self._suggestions)})")
        else:
            self._show_empty_state()

    def clear(self):
        """Clear all suggestions."""
        self._show_empty_state()

    def is_loading(self) -> bool:
        """Check if panel is in loading state."""
        return self._is_loading
