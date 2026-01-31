"""
Tests for core components: Button, Input, Card, Badge, Alert, etc.
"""

import pytest
from PySide6.QtCore import Qt

from design_system.components import (
    Alert,
    Avatar,
    Badge,
    Button,
    Card,
    Chip,
    FileIcon,
    Input,
    Label,
    Separator,
)

pytestmark = pytest.mark.unit  # All tests in this module are unit tests


class TestButton:
    """Tests for Button component."""

    def test_button_creation(self, qtbot):
        """Button should be created with default settings."""
        btn = Button("Click me")
        qtbot.addWidget(btn)

        assert btn.text() == "Click me"
        assert btn.cursor().shape() == Qt.CursorShape.PointingHandCursor

    @pytest.mark.parametrize(
        "variant",
        ["primary", "secondary", "outline", "ghost", "danger", "success"],
    )
    def test_button_variant(self, qtbot, variant):
        """Button should support different variants."""
        btn = Button("Test", variant=variant)
        qtbot.addWidget(btn)
        assert btn._variant == variant

    @pytest.mark.parametrize("size", ["sm", "md", "lg"])
    def test_button_size(self, qtbot, size):
        """Button should support different sizes."""
        btn = Button("Test", size=size)
        qtbot.addWidget(btn)
        assert btn._size == size

    def test_button_click(self, qtbot):
        """Button should emit clicked signal."""
        btn = Button("Click me")
        qtbot.addWidget(btn)

        with qtbot.waitSignal(btn.clicked, timeout=1000):
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)


class TestInput:
    """Tests for Input component."""

    def test_input_creation(self, qtbot):
        """Input should be created with placeholder."""
        inp = Input(placeholder="Enter text...")
        qtbot.addWidget(inp)

        assert inp.placeholderText() == "Enter text..."

    def test_input_text(self, qtbot):
        """Input should accept and return text."""
        inp = Input()
        qtbot.addWidget(inp)

        qtbot.keyClicks(inp, "Hello World")
        assert inp.text() == "Hello World"

    @pytest.mark.parametrize("error_state", [True, False])
    def test_input_error_state(self, qtbot, error_state):
        """Input should support error state."""
        inp = Input()
        qtbot.addWidget(inp)

        inp.set_error(error_state)
        assert inp.is_error() == error_state


class TestLabel:
    """Tests for Label component."""

    def test_label_creation(self, qtbot):
        """Label should display text."""
        label = Label("Test Label")
        qtbot.addWidget(label)

        assert label.text() == "Test Label"

    @pytest.mark.parametrize(
        "variant", ["default", "muted", "secondary", "title", "description"]
    )
    def test_label_variant(self, qtbot, variant):
        """Label should support variants."""
        label = Label("Test", variant=variant)
        qtbot.addWidget(label)
        # Variant is set as property for non-default
        if variant != "default":
            assert label.property("variant") == variant


class TestCard:
    """Tests for Card component."""

    def test_card_creation(self, qtbot):
        """Card should be created."""
        card = Card()
        qtbot.addWidget(card)

        assert card.layout() is not None

    @pytest.mark.parametrize(
        "shadow,has_effect",
        [(True, True), (False, False)],
    )
    def test_card_shadow(self, qtbot, shadow, has_effect):
        """Card shadow effect should be configurable."""
        card = Card(shadow=shadow)
        qtbot.addWidget(card)

        if has_effect:
            assert card.graphicsEffect() is not None
        else:
            assert card.graphicsEffect() is None


class TestBadge:
    """Tests for Badge component."""

    def test_badge_creation(self, qtbot):
        """Badge should display text."""
        badge = Badge("New")
        qtbot.addWidget(badge)

        assert badge.text() == "New"

    @pytest.mark.parametrize(
        "variant",
        ["default", "secondary", "success", "warning", "error", "info"],
    )
    def test_badge_variant(self, qtbot, variant):
        """Badge should support different variants."""
        badge = Badge("Test", variant=variant)
        qtbot.addWidget(badge)
        # Badge should be created without error
        assert badge is not None


class TestAlert:
    """Tests for Alert component."""

    def test_alert_creation(self, qtbot):
        """Alert should be created with title and description."""
        alert = Alert(title="Warning", description="This is a warning message")
        qtbot.addWidget(alert)

        # Alert should have content
        assert alert.layout() is not None
        assert alert.layout().count() > 0

    @pytest.mark.parametrize(
        "variant",
        ["default", "destructive", "success", "warning", "info"],
    )
    def test_alert_variant(self, qtbot, variant):
        """Alert should support different variants."""
        alert = Alert(title="Test", description="Test message", variant=variant)
        qtbot.addWidget(alert)
        # Should not crash
        assert alert is not None


class TestAvatar:
    """Tests for Avatar component."""

    def test_avatar_creation(self, qtbot):
        """Avatar should display initials."""
        avatar = Avatar("JD")
        qtbot.addWidget(avatar)

        assert avatar.text() == "JD"

    @pytest.mark.parametrize("size", [32, 48, 60, 80])
    def test_avatar_size(self, qtbot, size):
        """Avatar should respect size parameter."""
        avatar = Avatar("A", size=size)
        qtbot.addWidget(avatar)

        assert avatar.width() == size
        assert avatar.height() == size


class TestChip:
    """Tests for Chip component."""

    def test_chip_creation(self, qtbot):
        """Chip should display text."""
        chip = Chip("Category")
        qtbot.addWidget(chip)

        # Chip should have a label
        assert chip.layout().count() > 0

    def test_chip_closable(self, qtbot):
        """Closable chip should have close button."""
        chip = Chip("Tag", closable=True)
        qtbot.addWidget(chip)

        # Should have label + close button
        assert chip.layout().count() >= 2

    def test_chip_close_signal(self, qtbot):
        """Closable chip should emit close_clicked signal."""
        chip = Chip("Tag", closable=True)
        qtbot.addWidget(chip)

        # Find the close button and click it
        with qtbot.waitSignal(chip.close_clicked, timeout=1000):
            # The close button is the second widget
            close_btn = chip.layout().itemAt(1).widget()
            qtbot.mouseClick(close_btn, Qt.MouseButton.LeftButton)


class TestFileIcon:
    """Tests for FileIcon component."""

    @pytest.mark.parametrize("file_type", ["text", "audio", "video", "image", "pdf"])
    def test_file_icon_type(self, qtbot, file_type):
        """FileIcon should support different file types."""
        icon = FileIcon(file_type)
        qtbot.addWidget(icon)
        # Should not crash
        assert icon is not None

    @pytest.mark.parametrize("size", [24, 32, 48, 64])
    def test_file_icon_size(self, qtbot, size):
        """FileIcon should respect size parameter."""
        icon = FileIcon("text", size=size)
        qtbot.addWidget(icon)

        assert icon.width() == size
        assert icon.height() == size


class TestSeparator:
    """Tests for Separator component."""

    @pytest.mark.parametrize(
        "orientation,expected_dim",
        [("horizontal", "height"), ("vertical", "width")],
    )
    def test_separator_orientation(self, qtbot, orientation, expected_dim):
        """Separator should have correct dimension based on orientation."""
        sep = Separator(orientation=orientation)
        qtbot.addWidget(sep)

        if expected_dim == "height":
            assert sep.height() == 1
        else:
            assert sep.width() == 1
