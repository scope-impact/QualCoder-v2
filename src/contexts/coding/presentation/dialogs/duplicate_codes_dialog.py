"""
Duplicate Codes Dialog

Implements QC-028.08 Detect Duplicate Codes:
- AC #1: Agent can identify semantically similar codes
- AC #2: Agent can suggest merge candidates
- AC #3: Detection considers code names and usage
- AC #4: Researcher decides on merge actions

Architecture (fDDD):
- Dialog emits SIGNALS for operations (merge, dismiss, etc.)
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


class DuplicatePairCard(QFrame):
    """
    Card widget displaying a pair of potentially duplicate codes.

    Shows both codes side by side with similarity score and rationale.
    Allows merging in either direction or dismissing.
    """

    merge_requested = Signal(
        int, int
    )  # source_id, target_id (source merges into target)
    dismiss_requested = Signal(int, int)  # code_a_id, code_b_id

    def __init__(
        self,
        code_a_id: int,
        code_a_name: str,
        code_a_color: str,
        code_a_segments: int,
        code_b_id: int,
        code_b_name: str,
        code_b_color: str,
        code_b_segments: int,
        similarity: int,
        rationale: str,
        colors: ColorPalette,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors
        self._code_a_id = code_a_id
        self._code_b_id = code_b_id

        self._setup_ui(
            code_a_name,
            code_a_color,
            code_a_segments,
            code_b_name,
            code_b_color,
            code_b_segments,
            similarity,
            rationale,
        )

    def _setup_ui(
        self,
        code_a_name: str,
        code_a_color: str,
        code_a_segments: int,
        code_b_name: str,
        code_b_color: str,
        code_b_segments: int,
        similarity: int,
        rationale: str,
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
        layout.setSpacing(SPACING.md)

        # Similarity badge at top
        similarity_color = self._get_similarity_color(similarity)
        similarity_label = QLabel(f"{similarity}% Similar")
        similarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        similarity_label.setStyleSheet(f"""
            QLabel {{
                color: {similarity_color};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_semibold};
                background-color: {similarity_color}15;
                padding: {SPACING.xs}px {SPACING.md}px;
                border-radius: {RADIUS.sm}px;
            }}
        """)
        layout.addWidget(similarity_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Codes comparison row
        codes_row = QHBoxLayout()
        codes_row.setSpacing(SPACING.md)

        # Code A
        code_a_widget = self._create_code_widget(
            code_a_name, code_a_color, code_a_segments
        )
        codes_row.addWidget(code_a_widget, 1)

        # Arrow
        arrow = QLabel("⟷")
        arrow.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_disabled};
                font-size: {TYPOGRAPHY.text_lg}px;
            }}
        """)
        codes_row.addWidget(arrow, alignment=Qt.AlignmentFlag.AlignCenter)

        # Code B
        code_b_widget = self._create_code_widget(
            code_b_name, code_b_color, code_b_segments
        )
        codes_row.addWidget(code_b_widget, 1)

        layout.addLayout(codes_row)

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

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING.sm)

        # Merge A into B
        merge_a_btn = QPushButton(f"Keep '{code_b_name}'")
        merge_a_btn.setToolTip(f"Merge '{code_a_name}' into '{code_b_name}'")
        merge_a_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        merge_a_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        merge_a_btn.clicked.connect(
            lambda: self.merge_requested.emit(self._code_a_id, self._code_b_id)
        )
        btn_layout.addWidget(merge_a_btn)

        # Merge B into A
        merge_b_btn = QPushButton(f"Keep '{code_a_name}'")
        merge_b_btn.setToolTip(f"Merge '{code_b_name}' into '{code_a_name}'")
        merge_b_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        merge_b_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        merge_b_btn.clicked.connect(
            lambda: self.merge_requested.emit(self._code_b_id, self._code_a_id)
        )
        btn_layout.addWidget(merge_b_btn)

        btn_layout.addStretch()

        # Not duplicates
        dismiss_btn = QPushButton("Not Duplicates")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface};
            }}
        """)
        dismiss_btn.clicked.connect(
            lambda: self.dismiss_requested.emit(self._code_a_id, self._code_b_id)
        )
        btn_layout.addWidget(dismiss_btn)

        layout.addLayout(btn_layout)

    def _create_code_widget(self, name: str, color: str, segments: int) -> QFrame:
        """Create a widget displaying a code."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Name with color swatch
        name_row = QHBoxLayout()
        name_row.setSpacing(SPACING.xs)

        swatch = QFrame()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: {RADIUS.xs}px;
            }}
        """)
        name_row.addWidget(swatch)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
        """)
        name_row.addWidget(name_label, 1)

        layout.addLayout(name_row)

        # Segment count
        segments_label = QLabel(f"{segments} segments")
        segments_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_disabled};
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
        """)
        layout.addWidget(segments_label)

        return frame

    def _get_similarity_color(self, similarity: int) -> str:
        """Get color based on similarity level."""
        if similarity >= 90:
            return self._colors.error
        elif similarity >= 80:
            return self._colors.warning
        else:
            return self._colors.text_secondary


class DuplicateCodesDialog(QDialog):
    """
    Dialog for reviewing potential duplicate codes.

    Shows pairs of similar codes with merge/dismiss options.
    Sorted by similarity score (highest first).

    Signals:
        detect_duplicates_requested: Request to scan for duplicates
        merge_requested: Request to merge two codes
        dismiss_requested: Request to mark pair as not duplicates
    """

    # Request signals
    detect_duplicates_requested = Signal(float)  # threshold
    merge_requested = Signal(int, int)  # source_id, target_id
    dismiss_requested = Signal(int, int, str)  # code_a_id, code_b_id, reason

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._candidates: list[dict] = []
        self._cards: dict[tuple[int, int], DuplicatePairCard] = {}

        self.setWindowTitle("Duplicate Code Detection")
        self.setModal(True)
        self.setMinimumSize(550, 450)
        self.resize(650, 550)

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

        title = QLabel("Potential Duplicate Codes")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header.addWidget(title)

        desc = QLabel(
            "The AI has identified codes that may be duplicates. "
            "Review each pair and decide whether to merge or keep them separate."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(desc)

        layout.addLayout(header)

        # Stats bar
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(self._stats_label)

        # Candidates scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._candidates_container = QWidget()
        self._candidates_layout = QVBoxLayout(self._candidates_container)
        self._candidates_layout.setContentsMargins(0, 0, 0, 0)
        self._candidates_layout.setSpacing(SPACING.md)
        self._candidates_layout.addStretch()

        scroll.setWidget(self._candidates_container)
        layout.addWidget(scroll, 1)

        # Empty state
        self._empty_label = QLabel(
            "No duplicate candidates found. Click 'Scan' to check for duplicates."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_sm}px;
            padding: {SPACING.xl}px;
        """)
        self._candidates_layout.insertWidget(0, self._empty_label)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        scan_btn = QPushButton("Scan for Duplicates")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        scan_btn.clicked.connect(self._on_scan)
        btn_layout.addWidget(scan_btn)

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

    def _on_scan(self):
        """Handle scan button click."""
        self.detect_duplicates_requested.emit(0.8)  # Default threshold

    def _on_card_merge(self, source_id: int, target_id: int):
        """Handle merge request from card."""
        self.merge_requested.emit(source_id, target_id)
        self._remove_card(source_id, target_id)

    def _on_card_dismiss(self, code_a_id: int, code_b_id: int):
        """Handle dismiss request from card."""
        self.dismiss_requested.emit(code_a_id, code_b_id, "")
        self._remove_card(code_a_id, code_b_id)

    def _remove_card(self, code_a_id: int, code_b_id: int):
        """Remove a card from the UI."""
        key = (code_a_id, code_b_id)
        key_reverse = (code_b_id, code_a_id)

        for k in [key, key_reverse]:
            if k in self._cards:
                card = self._cards.pop(k)
                card.setParent(None)
                card.deleteLater()
                break

        self._update_stats()

        # Show empty state if no more cards
        if not self._cards:
            self._empty_label.setText("All duplicate candidates have been reviewed.")
            self._empty_label.show()

    def _update_stats(self):
        """Update the stats label."""
        count = len(self._cards)
        if count > 0:
            self._stats_label.setText(f"{count} potential duplicate pair(s) found")
        else:
            self._stats_label.setText("")

    # =========================================================================
    # Slots for receiving results from controller
    # =========================================================================

    def on_duplicates_detected(self, candidates: list[dict]):
        """
        Slot to receive duplicate candidates from controller.

        Args:
            candidates: List of candidate dicts with keys:
                - code_a_id: int
                - code_a_name: str
                - code_a_color: str (hex)
                - code_a_segments: int
                - code_b_id: int
                - code_b_name: str
                - code_b_color: str (hex)
                - code_b_segments: int
                - similarity: int (0-100)
                - rationale: str
        """
        self._candidates = candidates
        self._empty_label.hide()

        # Clear existing cards
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # Add new cards
        for cand in candidates:
            card = DuplicatePairCard(
                code_a_id=cand["code_a_id"],
                code_a_name=cand["code_a_name"],
                code_a_color=cand.get("code_a_color", "#888888"),
                code_a_segments=cand.get("code_a_segments", 0),
                code_b_id=cand["code_b_id"],
                code_b_name=cand["code_b_name"],
                code_b_color=cand.get("code_b_color", "#888888"),
                code_b_segments=cand.get("code_b_segments", 0),
                similarity=cand["similarity"],
                rationale=cand["rationale"],
                colors=self._colors,
            )
            card.merge_requested.connect(self._on_card_merge)
            card.dismiss_requested.connect(self._on_card_dismiss)

            key = (cand["code_a_id"], cand["code_b_id"])
            self._cards[key] = card
            # Insert before stretch
            self._candidates_layout.insertWidget(
                self._candidates_layout.count() - 1, card
            )

        self._update_stats()

        if not candidates:
            self._empty_label.setText(
                "No duplicate codes found. Your codebook is clean!"
            )
            self._empty_label.show()

    def on_merge_completed(self, source_id: int, target_id: int):
        """Slot to handle successful merge."""
        self._remove_card(source_id, target_id)

    def on_dismiss_completed(self, code_a_id: int, code_b_id: int):
        """Slot to handle successful dismissal."""
        self._remove_card(code_a_id, code_b_id)

    def on_error(self, operation: str, message: str):
        """Slot to receive error notifications."""
        # Could show error dialog here
        pass

    # =========================================================================
    # Public API for black-box testing
    # =========================================================================

    def get_candidate_count(self) -> int:
        """Get the number of duplicate candidate pairs currently displayed."""
        return len(self._cards)

    def request_merge(self, source_id: int, target_id: int) -> None:
        """
        Programmatically request a merge operation.

        This emits the merge_requested signal as if the user clicked the merge button.

        Args:
            source_id: ID of the code to merge from (will be deleted)
            target_id: ID of the code to merge into (will be kept)
        """
        self.merge_requested.emit(source_id, target_id)

    def request_dismiss(self, code_a_id: int, code_b_id: int) -> None:
        """
        Programmatically request a dismiss operation.

        This emits the dismiss_requested signal and removes the card from the UI.

        Args:
            code_a_id: ID of the first code in the pair
            code_b_id: ID of the second code in the pair
        """
        self.dismiss_requested.emit(code_a_id, code_b_id, "")
        self._remove_card(code_a_id, code_b_id)

    def request_scan(self) -> None:
        """
        Programmatically request a scan for duplicates.

        This calls the internal _on_scan method as if the user clicked the scan button.
        """
        self._on_scan()

    def is_empty_state_visible(self) -> bool:
        """Check if the empty state label is currently visible."""
        return self._empty_label.isVisible()
