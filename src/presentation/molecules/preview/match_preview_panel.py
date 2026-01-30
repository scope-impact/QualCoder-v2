"""
Match Preview Panel Molecule

A scrollable panel that displays a list of match previews with a summary header.
Used for previewing search results, auto-code matches, or any list of text matches.

Pure presentation component - receives match data, displays preview cards.
"""

from typing import Any

from PySide6.QtWidgets import (
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
    Card,
    ColorPalette,
    get_colors,
)


class MatchPreviewItem(Card):
    """
    Single match preview item showing index, position, and context.

    Extends design_system.Card for consistent styling.

    Displays:
    - Match index and position range
    - Context text (or matched text if no context provided)

    Example:
        match = {"start": 10, "end": 20, "context": "...highlighted text..."}
        item = MatchPreviewItem(index=1, match=match)
    """

    def __init__(
        self,
        index: int,
        match: dict[str, Any],
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the match preview item.

        Args:
            index: 1-based index of the match
            match: Dictionary with match data:
                - start: Start position in text
                - end: End position in text
                - text: The matched text
                - context: Optional surrounding context
            colors: Color palette for styling
            parent: Parent widget
        """
        self._colors = colors or get_colors()
        super().__init__(colors=self._colors, parent=parent, shadow=False, elevation=1)
        self._index = index
        self._match = match

        self._setup_ui()

    def _setup_ui(self):
        """Build the item UI using Card's layout."""
        # Override Card's default styling for compact preview items
        self.setStyleSheet(f"""
            MatchPreviewItem {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
                border: none;
            }}
        """)

        # Adjust Card's default margins for compact display
        self._layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        self._layout.setSpacing(2)

        # Index and position header
        start = self._match.get("start", 0)
        end = self._match.get("end", 0)
        header = QLabel(f"#{self._index} (pos {start}-{end})")
        header.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        self._layout.addWidget(header)

        # Context with matched text
        context = self._match.get("context", self._match.get("text", ""))
        context_label = QLabel(context)
        context_label.setWordWrap(True)
        context_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        self._layout.addWidget(context_label)

    def get_index(self) -> int:
        """Get the match index."""
        return self._index

    def get_match(self) -> dict[str, Any]:
        """Get the match data."""
        return self._match


class MatchPreviewPanel(Card):
    """
    Scrollable panel showing match previews with summary header.

    Extends design_system.Card for consistent styling.

    Displays:
    - Summary header with match count ("X matches found")
    - Scrollable list of MatchPreviewItem cards

    Example:
        panel = MatchPreviewPanel()
        matches = [
            {"start": 0, "end": 10, "text": "hello", "context": "...hello world..."},
            {"start": 50, "end": 60, "text": "hello", "context": "...say hello..."},
        ]
        panel.set_matches(matches)
        print(panel.get_match_count())  # 2
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the match preview panel.

        Args:
            colors: Color palette for styling
            parent: Parent widget
        """
        self._colors = colors or get_colors()
        super().__init__(colors=self._colors, parent=parent, shadow=False, elevation=1)
        self._matches: list[dict[str, Any]] = []
        self._items: list[MatchPreviewItem] = []

        self._setup_ui()

    def _setup_ui(self):
        """Build the panel UI using Card's base styling."""
        # Card provides base styling; adjust margins for panel layout
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header with summary
        header = Card(colors=self._colors, shadow=False)
        header.setStyleSheet(f"""
            Card {{
                background-color: {self._colors.surface_light};
                border: none;
                border-bottom: 1px solid {self._colors.border};
                border-radius: 0;
            }}
        """)
        header._layout.setContentsMargins(
            SPACING.md, SPACING.sm, SPACING.md, SPACING.sm
        )

        self._summary_label = QLabel("No matches")
        self._summary_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header_inner = QHBoxLayout()
        header_inner.addWidget(self._summary_label)
        header_inner.addStretch()
        header._layout.addLayout(header_inner)

        self._layout.addWidget(header)

        # Scrollable match list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self._colors.surface};
            }}
        """)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(
            SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm
        )
        self._list_layout.setSpacing(SPACING.xs)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        self._layout.addWidget(scroll, 1)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_matches(self, matches: list[dict[str, Any]]):
        """
        Set the matches to preview.

        Args:
            matches: List of match dicts with 'start', 'end', 'text', 'context' keys
        """
        self._matches = matches

        # Clear existing items
        for item in self._items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

        # Update summary
        count = len(matches)
        self._summary_label.setText(f"{count} match{'es' if count != 1 else ''} found")

        # Add new match items
        for i, match in enumerate(matches):
            item = MatchPreviewItem(
                index=i + 1,
                match=match,
                colors=self._colors,
            )
            self._items.append(item)
            # Insert before the stretch
            self._list_layout.insertWidget(self._list_layout.count() - 1, item)

    def clear_matches(self):
        """Clear all matches."""
        self.set_matches([])

    def get_match_count(self) -> int:
        """Get the number of matches."""
        return len(self._matches)

    def get_matches(self) -> list[dict[str, Any]]:
        """Get all matches."""
        return self._matches.copy()

    def get_summary_text(self) -> str:
        """Get the summary label text."""
        return self._summary_label.text()


# Backward compatibility alias
AutoCodePreview = MatchPreviewPanel
