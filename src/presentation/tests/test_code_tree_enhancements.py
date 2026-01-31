"""
Tests for QC-007.06 Code Tree Enhancements

Tests enhancements to the codes panel:
- AC #1: Context menu for code operations
- AC #2: Drag-and-drop reorganization
- AC #3: Code search/filter input
- AC #4: Sort options (name/count/color)
- AC #5: Selection tracking
- AC #6: Recent codes tracking (last 10)
- AC #7: Important codes filter toggle
"""

from PySide6.QtTest import QSignalSpy


class TestCodeTreeFilter:
    """Tests for code tree filtering functionality."""

    def test_filter_by_name(self, qapp, colors):
        """Filter shows only codes matching search query."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Themes",
                    "codes": [
                        {"id": "1", "name": "Identity", "color": "#FF0000", "count": 5},
                        {
                            "id": "2",
                            "name": "Community",
                            "color": "#00FF00",
                            "count": 3,
                        },
                        {"id": "3", "name": "Work", "color": "#0000FF", "count": 2},
                    ],
                }
            ]
        )

        panel.set_filter_text("iden")

        # Only Identity should be visible
        visible = panel.get_visible_code_count()
        assert visible == 1

    def test_filter_shows_matching_codes(self, qapp, colors):
        """Filter matches partial names case-insensitively."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "All Codes",
                    "codes": [
                        {"id": "1", "name": "Theme: Identity", "color": "#FF0000"},
                        {"id": "2", "name": "Sub-Identity", "color": "#00FF00"},
                        {"id": "3", "name": "Work Context", "color": "#0000FF"},
                    ],
                }
            ]
        )

        panel.set_filter_text("IDENTITY")  # Uppercase

        visible = panel.get_visible_code_count()
        assert visible == 2  # Both codes with "Identity"

    def test_filter_hides_non_matching(self, qapp, colors):
        """Non-matching codes are hidden."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {"id": "1", "name": "Apple", "color": "#FF0000"},
                        {"id": "2", "name": "Banana", "color": "#00FF00"},
                        {"id": "3", "name": "Cherry", "color": "#0000FF"},
                    ],
                }
            ]
        )

        panel.set_filter_text("xyz")

        visible = panel.get_visible_code_count()
        assert visible == 0

    def test_clear_filter_shows_all(self, qapp, colors):
        """Clearing filter shows all codes."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {"id": "1", "name": "A", "color": "#FF0000"},
                        {"id": "2", "name": "B", "color": "#00FF00"},
                    ],
                }
            ]
        )

        panel.set_filter_text("A")
        assert panel.get_visible_code_count() == 1

        panel.set_filter_text("")
        assert panel.get_visible_code_count() == 2


class TestCodeTreeSort:
    """Tests for code tree sorting functionality."""

    def test_sort_by_name(self, qapp, colors):
        """Codes can be sorted alphabetically by name."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {"id": "1", "name": "Zebra", "color": "#FF0000", "count": 1},
                        {"id": "2", "name": "Apple", "color": "#00FF00", "count": 2},
                        {"id": "3", "name": "Mango", "color": "#0000FF", "count": 3},
                    ],
                }
            ]
        )

        panel.set_sort_mode("name")
        codes = panel.get_sorted_codes()

        assert codes[0]["name"] == "Apple"
        assert codes[1]["name"] == "Mango"
        assert codes[2]["name"] == "Zebra"

    def test_sort_by_count(self, qapp, colors):
        """Codes can be sorted by usage count (descending)."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {"id": "1", "name": "A", "color": "#FF0000", "count": 5},
                        {"id": "2", "name": "B", "color": "#00FF00", "count": 10},
                        {"id": "3", "name": "C", "color": "#0000FF", "count": 3},
                    ],
                }
            ]
        )

        panel.set_sort_mode("count")
        codes = panel.get_sorted_codes()

        assert codes[0]["count"] == 10
        assert codes[1]["count"] == 5
        assert codes[2]["count"] == 3


class TestRecentCodes:
    """Tests for recent codes tracking."""

    def test_recent_codes_tracks_used(self, qapp, colors):
        """Recently used codes are tracked."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {"id": "1", "name": "Code A", "color": "#FF0000"},
                        {"id": "2", "name": "Code B", "color": "#00FF00"},
                    ],
                }
            ]
        )

        panel.add_to_recent({"id": "1", "name": "Code A", "color": "#FF0000"})
        panel.add_to_recent({"id": "2", "name": "Code B", "color": "#00FF00"})

        recent = panel.get_recent_codes()
        assert len(recent) == 2
        # Most recent first
        assert recent[0]["id"] == "2"

    def test_recent_codes_max_10(self, qapp, colors):
        """Recent codes list is capped at 10."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)

        for i in range(15):
            panel.add_to_recent({"id": str(i), "name": f"Code {i}", "color": "#FF0000"})

        recent = panel.get_recent_codes()
        assert len(recent) == 10
        # Most recent should be Code 14
        assert recent[0]["id"] == "14"

    def test_recent_codes_no_duplicates(self, qapp, colors):
        """Same code used twice moves to top, no duplicates."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)

        panel.add_to_recent({"id": "1", "name": "Code A", "color": "#FF0000"})
        panel.add_to_recent({"id": "2", "name": "Code B", "color": "#00FF00"})
        panel.add_to_recent({"id": "1", "name": "Code A", "color": "#FF0000"})

        recent = panel.get_recent_codes()
        assert len(recent) == 2
        assert recent[0]["id"] == "1"  # Moved to top


class TestCodeTreeDragDrop:
    """Tests for drag and drop functionality."""

    def test_drag_drop_emits_move_signal(self, qapp, colors):
        """Drag and drop emits move signal."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        spy = QSignalSpy(panel.code_move_requested)

        # Simulate move request
        panel.request_code_move("code1", "category2")

        assert spy.count() == 1
        assert spy.at(0)[0] == "code1"
        assert spy.at(0)[1] == "category2"

    def test_drag_enabled_on_codes(self, qapp, colors):
        """Codes can be dragged."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Cat1",
                    "codes": [{"id": "1", "name": "Code", "color": "#FF0000"}],
                }
            ]
        )

        assert panel.is_drag_enabled()


class TestSelectionTracking:
    """Tests for selection tracking."""

    def test_get_selected_code(self, qapp, colors):
        """Can retrieve currently selected code."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [{"id": "1", "name": "Test", "color": "#FF0000"}],
                }
            ]
        )

        # Simulate selection
        panel._on_code_click("1")

        selected = panel.get_selected_code()
        assert selected.get("id") == "1"

    def test_selection_signal_emitted(self, qapp, colors):
        """Selection emits signal with code data."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        spy = QSignalSpy(panel.code_selected)

        panel._on_code_click("1")

        assert spy.count() == 1


class TestImportantFilter:
    """Tests for important codes filter."""

    def test_important_filter_toggle(self, qapp, colors):
        """Can toggle important codes filter."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)

        assert not panel.is_important_filter_active()

        panel.set_important_filter(True)
        assert panel.is_important_filter_active()

        panel.set_important_filter(False)
        assert not panel.is_important_filter_active()

    def test_important_filter_shows_only_important(self, qapp, colors):
        """Important filter shows only codes with important segments."""
        from src.presentation.organisms.codes_panel import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Codes",
                    "codes": [
                        {
                            "id": "1",
                            "name": "A",
                            "color": "#FF0000",
                            "has_important": True,
                        },
                        {
                            "id": "2",
                            "name": "B",
                            "color": "#00FF00",
                            "has_important": False,
                        },
                    ],
                }
            ]
        )

        panel.set_important_filter(True)

        visible = panel.get_visible_code_count()
        assert visible == 1
