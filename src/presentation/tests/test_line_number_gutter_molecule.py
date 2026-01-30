"""
Tests for LineNumberGutter Molecule

Tests the pure presentation behavior of the LineNumberGutter component.
This is a molecule-level test - it tests the component in isolation.
"""


class TestLineNumberGutterMolecule:
    """Unit tests for LineNumberGutter molecule."""

    def test_imports_from_molecules_package(self, qapp, colors):
        """LineNumberGutter can be imported from molecules package."""
        from src.presentation.molecules import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert gutter is not None

    def test_imports_from_editor_subpackage(self, qapp, colors):
        """LineNumberGutter can be imported from editor subpackage."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert gutter is not None

    def test_default_line_count_is_one(self, qapp, colors):
        """Default line count is 1."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert gutter.get_line_count() == 1

    def test_set_line_count_updates_display(self, qapp, colors):
        """set_line_count() updates the number of labels."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(10)

        assert gutter.get_line_count() == 10

    def test_set_line_count_minimum_is_one(self, qapp, colors):
        """Line count cannot be less than 1."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(0)

        assert gutter.get_line_count() == 1

    def test_set_line_count_negative_becomes_one(self, qapp, colors):
        """Negative line count becomes 1."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(-5)

        assert gutter.get_line_count() == 1

    def test_labels_are_created_lazily(self, qapp, colors):
        """Labels are created on demand."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert len(gutter._labels) == 0

        gutter.set_line_count(5)
        assert len(gutter._labels) == 5

    def test_labels_are_reused(self, qapp, colors):
        """Existing labels are reused when count decreases then increases."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(10)
        assert len(gutter._labels) == 10

        gutter.set_line_count(5)
        # Labels still exist, just hidden
        assert len(gutter._labels) == 10

        gutter.set_line_count(8)
        # No new labels created
        assert len(gutter._labels) == 10

    def test_labels_visibility_matches_count(self, qapp, colors):
        """Only the first N labels should be visible (hidden via setVisible)."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(10)
        gutter.set_line_count(5)

        # Check that labels after index 5 are hidden
        # Note: isVisible() returns False if parent not shown, so check isHidden()
        for i, label in enumerate(gutter._labels):
            if i < 5:
                assert not label.isHidden(), f"Label {i} should not be hidden"
            else:
                assert label.isHidden(), f"Label {i} should be hidden"

    def test_fixed_width(self, qapp, colors):
        """Gutter has a fixed width."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert gutter.width() == 50 or gutter.minimumWidth() == 50

    def test_default_line_height(self, qapp, colors):
        """Default line height is 22 pixels."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        assert gutter.get_line_height() == 22

    def test_set_line_height(self, qapp, colors):
        """set_line_height() updates label heights."""
        from src.presentation.molecules.editor import LineNumberGutter

        gutter = LineNumberGutter(colors=colors)
        gutter.set_line_count(3)
        gutter.set_line_height(30)

        assert gutter.get_line_height() == 30
        for label in gutter._labels:
            assert label.height() == 30


class TestBackwardCompatibility:
    """Tests for backward compatibility with LineNumberWidget alias."""

    def test_linenumberwidget_alias_available(self, qapp, colors):
        """LineNumberWidget alias is available from text_editor_panel."""
        from src.presentation.organisms.text_editor_panel import LineNumberWidget

        widget = LineNumberWidget(colors=colors)
        assert widget is not None

    def test_linenumberwidget_is_linenumbergutter(self, qapp, colors):
        """LineNumberWidget is the same class as LineNumberGutter."""
        from src.presentation.molecules.editor import LineNumberGutter
        from src.presentation.organisms.text_editor_panel import LineNumberWidget

        assert LineNumberWidget is LineNumberGutter
