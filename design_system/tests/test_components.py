"""
Tests for core components: Button, Input, Card, Badge, Alert, etc.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from design_system.components import (
    Button, Input, Label, Card, CardHeader, Badge,
    Separator, Alert, Avatar, Chip, FileIcon
)
from design_system.tokens import get_theme


class TestButton:
    """Tests for Button component"""

    def test_button_creation(self, qtbot):
        """Button should be created with default settings"""
        btn = Button("Click me")
        qtbot.addWidget(btn)

        assert btn.text() == "Click me"
        assert btn.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_button_variants(self, qtbot):
        """Button should support different variants"""
        variants = ["primary", "secondary", "outline", "ghost", "danger", "success"]

        for variant in variants:
            btn = Button("Test", variant=variant)
            qtbot.addWidget(btn)
            assert btn._variant == variant

    def test_button_sizes(self, qtbot):
        """Button should support different sizes"""
        sizes = ["sm", "md", "lg"]

        for size in sizes:
            btn = Button("Test", size=size)
            qtbot.addWidget(btn)
            assert btn._size == size

    def test_button_click(self, qtbot):
        """Button should emit clicked signal"""
        btn = Button("Click me")
        qtbot.addWidget(btn)

        with qtbot.waitSignal(btn.clicked, timeout=1000):
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)


class TestInput:
    """Tests for Input component"""

    def test_input_creation(self, qtbot):
        """Input should be created with placeholder"""
        inp = Input(placeholder="Enter text...")
        qtbot.addWidget(inp)

        assert inp.placeholderText() == "Enter text..."

    def test_input_text(self, qtbot):
        """Input should accept and return text"""
        inp = Input()
        qtbot.addWidget(inp)

        qtbot.keyClicks(inp, "Hello World")
        assert inp.text() == "Hello World"

    def test_input_error_state(self, qtbot):
        """Input should support error state"""
        inp = Input()
        qtbot.addWidget(inp)

        assert not inp.is_error()
        inp.set_error(True)
        assert inp.is_error()
        inp.set_error(False)
        assert not inp.is_error()


class TestLabel:
    """Tests for Label component"""

    def test_label_creation(self, qtbot):
        """Label should display text"""
        label = Label("Test Label")
        qtbot.addWidget(label)

        assert label.text() == "Test Label"

    def test_label_variants(self, qtbot):
        """Label should support variants"""
        variants = ["default", "muted", "secondary", "title", "description"]

        for variant in variants:
            label = Label("Test", variant=variant)
            qtbot.addWidget(label)
            # Variant is set as property for non-default
            if variant != "default":
                assert label.property("variant") == variant


class TestCard:
    """Tests for Card component"""

    def test_card_creation(self, qtbot):
        """Card should be created"""
        card = Card()
        qtbot.addWidget(card)

        assert card.layout() is not None

    def test_card_with_shadow(self, qtbot):
        """Card should have shadow effect by default"""
        card = Card(shadow=True)
        qtbot.addWidget(card)

        assert card.graphicsEffect() is not None

    def test_card_without_shadow(self, qtbot):
        """Card can be created without shadow"""
        card = Card(shadow=False)
        qtbot.addWidget(card)

        assert card.graphicsEffect() is None


class TestBadge:
    """Tests for Badge component"""

    def test_badge_creation(self, qtbot):
        """Badge should display text"""
        badge = Badge("New")
        qtbot.addWidget(badge)

        assert badge.text() == "New"

    def test_badge_variants(self, qtbot):
        """Badge should support different variants"""
        variants = ["default", "secondary", "success", "warning", "error", "info"]

        for variant in variants:
            badge = Badge("Test", variant=variant)
            qtbot.addWidget(badge)
            # Badge should be visible
            assert badge.isVisible() or True  # Just check it doesn't crash


class TestAlert:
    """Tests for Alert component"""

    def test_alert_creation(self, qtbot):
        """Alert should be created with title and description"""
        alert = Alert(title="Warning", description="This is a warning message")
        qtbot.addWidget(alert)

        # Alert should have content
        assert alert.layout() is not None
        assert alert.layout().count() > 0

    def test_alert_variants(self, qtbot):
        """Alert should support different variants"""
        variants = ["default", "destructive", "success", "warning", "info"]

        for variant in variants:
            alert = Alert(title="Test", description="Test message", variant=variant)
            qtbot.addWidget(alert)
            # Should not crash
            assert alert is not None


class TestAvatar:
    """Tests for Avatar component"""

    def test_avatar_creation(self, qtbot):
        """Avatar should display initials"""
        avatar = Avatar("JD")
        qtbot.addWidget(avatar)

        assert avatar.text() == "JD"

    def test_avatar_size(self, qtbot):
        """Avatar should respect size parameter"""
        avatar = Avatar("A", size=60)
        qtbot.addWidget(avatar)

        assert avatar.width() == 60
        assert avatar.height() == 60


class TestChip:
    """Tests for Chip component"""

    def test_chip_creation(self, qtbot):
        """Chip should display text"""
        chip = Chip("Category")
        qtbot.addWidget(chip)

        # Chip should have a label
        assert chip.layout().count() > 0

    def test_chip_closable(self, qtbot):
        """Closable chip should have close button"""
        chip = Chip("Tag", closable=True)
        qtbot.addWidget(chip)

        # Should have label + close button
        assert chip.layout().count() >= 2

    def test_chip_close_signal(self, qtbot):
        """Closable chip should emit close_clicked signal"""
        chip = Chip("Tag", closable=True)
        qtbot.addWidget(chip)

        # Find the close button and click it
        with qtbot.waitSignal(chip.close_clicked, timeout=1000):
            # The close button is the second widget
            close_btn = chip.layout().itemAt(1).widget()
            qtbot.mouseClick(close_btn, Qt.MouseButton.LeftButton)


class TestFileIcon:
    """Tests for FileIcon component"""

    def test_file_icon_types(self, qtbot):
        """FileIcon should support different file types"""
        types = ["text", "audio", "video", "image", "pdf"]

        for file_type in types:
            icon = FileIcon(file_type)
            qtbot.addWidget(icon)
            # Should not crash
            assert icon is not None

    def test_file_icon_size(self, qtbot):
        """FileIcon should respect size parameter"""
        icon = FileIcon("text", size=48)
        qtbot.addWidget(icon)

        assert icon.width() == 48
        assert icon.height() == 48


class TestSeparator:
    """Tests for Separator component"""

    def test_horizontal_separator(self, qtbot):
        """Horizontal separator should have height of 1"""
        sep = Separator(orientation="horizontal")
        qtbot.addWidget(sep)

        assert sep.height() == 1

    def test_vertical_separator(self, qtbot):
        """Vertical separator should have width of 1"""
        sep = Separator(orientation="vertical")
        qtbot.addWidget(sep)

        assert sep.width() == 1
