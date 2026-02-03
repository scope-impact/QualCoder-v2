"""
Code Suggestion Dialog

Implements QC-028.07 Suggest New Code:
- AC #1: Agent can analyze uncoded text content
- AC #2: Agent can propose new codes with rationale
- AC #3: Agent can suggest appropriate colors
- AC #4: Researcher reviews and approves/modifies suggestions

Architecture (fDDD):
- Dialog emits SIGNALS for operations (approve, reject, etc.)
- Controller receives signals, calls domain services
- Controller emits result PAYLOADS via signal bridge
- Dialog receives payloads and updates UI

This follows proper fDDD decoupling - presentation NEVER imports domain.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
)


class SuggestionCard(QFrame):
    """
    Card widget displaying a single code suggestion.

    Shows name, color, confidence, and rationale.
    Allows editing name before approval.
    """

    approve_clicked = Signal(str, str, str)  # suggestion_id, name, color
    reject_clicked = Signal(str, str)  # suggestion_id, reason

    def __init__(
        self,
        suggestion_id: str,
        name: str,
        color: str,
        rationale: str,
        confidence: int,
        contexts: list[str],
        colors: ColorPalette,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors
        self._suggestion_id = suggestion_id
        self._original_name = name
        self._color = color

        self._setup_ui(name, color, rationale, confidence, contexts)

    def _setup_ui(
        self,
        name: str,
        color: str,
        rationale: str,
        confidence: int,
        contexts: list[str],
    ):
        """Build the card UI."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        # Header with color and confidence
        header = QHBoxLayout()

        # Color swatch
        swatch = QFrame()
        swatch.setFixedSize(24, 24)
        swatch.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        header.addWidget(swatch)

        # Name input
        self._name_input = QLineEdit(name)
        self._name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        header.addWidget(self._name_input, 1)

        # Confidence badge
        confidence_label = QLabel(f"{confidence}%")
        confidence_color = self._get_confidence_color(confidence)
        confidence_label.setStyleSheet(f"""
            QLabel {{
                color: {confidence_color};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_semibold};
                background-color: {confidence_color}20;
                padding: {SPACING.xs}px {SPACING.sm}px;
                border-radius: {RADIUS.sm}px;
            }}
        """)
        header.addWidget(confidence_label)

        layout.addLayout(header)

        # Rationale
        rationale_label = QLabel(rationale)
        rationale_label.setWordWrap(True)
        rationale_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        layout.addWidget(rationale_label)

        # Context excerpts (if any)
        if contexts:
            context_label = QLabel("Supporting text:")
            context_label.setStyleSheet(f"""
                QLabel {{
                    color: {self._colors.text_disabled};
                    font-size: {TYPOGRAPHY.text_xs}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
            layout.addWidget(context_label)

            for ctx in contexts[:2]:  # Show max 2 contexts
                excerpt = QLabel(f'"{ctx[:100]}..."' if len(ctx) > 100 else f'"{ctx}"')
                excerpt.setWordWrap(True)
                excerpt.setStyleSheet(f"""
                    QLabel {{
                        color: {self._colors.text_secondary};
                        font-size: {TYPOGRAPHY.text_xs}px;
                        font-style: italic;
                        background-color: {self._colors.surface};
                        padding: {SPACING.xs}px;
                        border-radius: {RADIUS.xs}px;
                    }}
                """)
                layout.addWidget(excerpt)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reject_btn = QPushButton("Reject")
        reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reject_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.error};
                border: 1px solid {self._colors.error};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.error}10;
            }}
        """)
        reject_btn.clicked.connect(self._on_reject)
        btn_layout.addWidget(reject_btn)

        approve_btn = QPushButton("Approve")
        approve_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        approve_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.success};
                color: white;
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.success}dd;
            }}
        """)
        approve_btn.clicked.connect(self._on_approve)
        btn_layout.addWidget(approve_btn)

        layout.addLayout(btn_layout)

    def _get_confidence_color(self, confidence: int) -> str:
        """Get color based on confidence level."""
        if confidence >= 80:
            return self._colors.success
        elif confidence >= 60:
            return self._colors.warning
        else:
            return self._colors.error

    def _on_approve(self):
        """Handle approve button click."""
        current_name = self._name_input.text().strip()
        if not current_name:
            current_name = self._original_name
        self.approve_clicked.emit(self._suggestion_id, current_name, self._color)

    def _on_reject(self):
        """Handle reject button click."""
        self.reject_clicked.emit(self._suggestion_id, "")

    # =========================================================================
    # Public API for black-box testing
    # =========================================================================

    def set_name(self, name: str) -> None:
        """
        Set the name in the input field.

        BLACK-BOX API: Encapsulates access to the private _name_input widget.

        Args:
            name: The name to set
        """
        self._name_input.setText(name)

    def get_name(self) -> str:
        """
        Get the current name from the input field.

        BLACK-BOX API: Encapsulates access to the private _name_input widget.

        Returns:
            The current name text
        """
        return self._name_input.text()

    def approve(self) -> None:
        """
        Programmatically approve this suggestion.

        BLACK-BOX API: Triggers approval as if the user clicked the approve button.
        """
        self._on_approve()

    def reject(self) -> None:
        """
        Programmatically reject this suggestion.

        BLACK-BOX API: Triggers rejection as if the user clicked the reject button.
        """
        self._on_reject()


class CodeSuggestionDialog(QDialog):
    """
    Dialog for reviewing AI code suggestions.

    Shows a list of suggested codes with rationale and context.
    Allows researcher to approve, modify, or reject each suggestion.

    Signals:
        suggest_codes_requested: Request to analyze text for suggestions
        approve_suggestion_requested: Request to approve a suggestion
        reject_suggestion_requested: Request to reject a suggestion
        approve_all_requested: Request to approve all pending suggestions
    """

    # Request signals
    suggest_codes_requested = Signal(str, int)  # text, source_id
    approve_suggestion_requested = Signal(str, str, str, str)  # id, name, color, memo
    reject_suggestion_requested = Signal(str, str)  # id, reason
    approve_all_requested = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._suggestions: list[dict] = []
        self._cards: dict[str, SuggestionCard] = {}

        self.setWindowTitle("AI Code Suggestions")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Title and description
        header = QVBoxLayout()
        header.setSpacing(SPACING.xs)

        title = QLabel("AI Code Suggestions")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header.addWidget(title)

        desc = QLabel(
            "The AI has analyzed your text and suggests the following codes. "
            "Review each suggestion and approve or reject."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(desc)

        layout.addLayout(header)

        # Suggestions scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._suggestions_container = QWidget()
        self._suggestions_layout = QVBoxLayout(self._suggestions_container)
        self._suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self._suggestions_layout.setSpacing(SPACING.md)
        self._suggestions_layout.addStretch()

        scroll.setWidget(self._suggestions_container)
        layout.addWidget(scroll, 1)

        # Empty state
        self._empty_label = QLabel(
            "No suggestions yet. Click 'Analyze' to get AI suggestions."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_sm}px;
            padding: {SPACING.xl}px;
        """)
        self._suggestions_layout.insertWidget(0, self._empty_label)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        approve_all_btn = QPushButton("Approve All")
        approve_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        approve_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_light};
                color: {self._colors.success};
                border: 1px solid {self._colors.success};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.success}10;
            }}
        """)
        approve_all_btn.clicked.connect(self._on_approve_all)
        btn_layout.addWidget(approve_all_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _on_approve_all(self):
        """Handle approve all button click."""
        self.approve_all_requested.emit()

    def _on_card_approved(self, suggestion_id: str, name: str, color: str):
        """Handle card approval."""
        self.approve_suggestion_requested.emit(suggestion_id, name, color, "")
        self._remove_card(suggestion_id)

    def _on_card_rejected(self, suggestion_id: str, reason: str):
        """Handle card rejection."""
        self.reject_suggestion_requested.emit(suggestion_id, reason)
        self._remove_card(suggestion_id)

    def _remove_card(self, suggestion_id: str):
        """Remove a card from the UI."""
        if suggestion_id in self._cards:
            card = self._cards.pop(suggestion_id)
            card.setParent(None)
            card.deleteLater()

        # Show empty state if no more cards
        if not self._cards:
            self._empty_label.show()

    # =========================================================================
    # Slots for receiving results from controller
    # =========================================================================

    def on_suggestions_received(self, suggestions: list[dict]):
        """
        Slot to receive suggestions from controller.

        Args:
            suggestions: List of suggestion dicts with keys:
                - suggestion_id: str
                - name: str
                - color: str (hex)
                - rationale: str
                - confidence: int (0-100)
                - contexts: list[str]
        """
        self._suggestions = suggestions
        self._empty_label.hide()

        # Clear existing cards
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # Add new cards
        for sug in suggestions:
            card = SuggestionCard(
                suggestion_id=sug["suggestion_id"],
                name=sug["name"],
                color=sug["color"],
                rationale=sug["rationale"],
                confidence=sug["confidence"],
                contexts=sug.get("contexts", []),
                colors=self._colors,
            )
            card.approve_clicked.connect(self._on_card_approved)
            card.reject_clicked.connect(self._on_card_rejected)

            self._cards[sug["suggestion_id"]] = card
            # Insert before stretch
            self._suggestions_layout.insertWidget(
                self._suggestions_layout.count() - 1, card
            )

        if not suggestions:
            self._empty_label.setText("No code suggestions found for this text.")
            self._empty_label.show()

    def on_suggestion_approved(self, suggestion_id: str):
        """Slot to handle successful approval."""
        self._remove_card(suggestion_id)

    def on_suggestion_rejected(self, suggestion_id: str):
        """Slot to handle successful rejection."""
        self._remove_card(suggestion_id)

    def on_error(self, operation: str, message: str):
        """Slot to receive error notifications."""
        # Could show error dialog here
        pass

    # =========================================================================
    # Public API for black-box testing
    # =========================================================================

    def get_suggestion_count(self) -> int:
        """Get the number of suggestions currently displayed."""
        return len(self._cards)

    def set_suggestion_name(self, suggestion_id: str, name: str) -> None:
        """
        Set the name input for a suggestion card.

        Args:
            suggestion_id: ID of the suggestion
            name: The name to set in the input field
        """
        if suggestion_id in self._cards:
            self._cards[suggestion_id].set_name(name)

    def get_suggestion_name(self, suggestion_id: str) -> str | None:
        """
        Get the current name from a suggestion card's input field.

        Args:
            suggestion_id: ID of the suggestion

        Returns:
            The current name in the input field, or None if suggestion not found
        """
        if suggestion_id in self._cards:
            return self._cards[suggestion_id].get_name()
        return None

    def approve_suggestion(self, suggestion_id: str) -> None:
        """
        Programmatically approve a suggestion.

        Triggers approval as if the user clicked the approve button on the card.

        Args:
            suggestion_id: ID of the suggestion to approve
        """
        if suggestion_id in self._cards:
            self._cards[suggestion_id].approve()

    def reject_suggestion(self, suggestion_id: str) -> None:
        """
        Programmatically reject a suggestion.

        Triggers rejection as if the user clicked the reject button on the card.

        Args:
            suggestion_id: ID of the suggestion to reject
        """
        if suggestion_id in self._cards:
            self._cards[suggestion_id].reject()

    def approve_all(self) -> None:
        """
        Programmatically approve all suggestions.

        This calls the internal _on_approve_all method as if the user clicked
        the 'Approve All' button.
        """
        self._on_approve_all()

    def is_empty_state_visible(self) -> bool:
        """Check if the empty state label is currently visible."""
        return self._empty_label.isVisible()
