"""
Tests for QC-007.09 Search in Text

Tests the search functionality in the text editor panel:
- AC #1: Search text finds matches
- AC #2: Highlights are applied to matches
- AC #3: Navigate to next match
- AC #4: Navigate to previous match
- AC #5: Case sensitive search option
- AC #6: Regex search support
- AC #7: Clear search removes highlights
- AC #8: Match counter shows current/total
"""

from PySide6.QtTest import QSignalSpy


class TestSearchInText:
    """Tests for search functionality in TextEditorPanel."""

    def test_search_text_finds_matches(self, qapp, colors):
        """AC #1: search_text() returns list of match positions."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document(
            "Test",
            text="The quick brown fox jumps over the lazy dog. The fox is quick.",
        )

        matches = panel.search_text("fox")

        assert len(matches) == 2
        assert matches[0] == (16, 19)  # First "fox"
        assert matches[1] == (49, 52)  # Second "fox"

    def test_search_text_no_matches(self, qapp, colors):
        """search_text() returns empty list when no matches found."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="Hello world")

        matches = panel.search_text("xyz")

        assert matches == []

    def test_search_text_highlights_matches(self, qapp, colors):
        """AC #2: search_text() highlights all matches in the document."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="apple banana apple cherry apple")

        panel.search_text("apple")

        # Check highlights were applied
        assert panel.get_search_highlight_count() == 3

    def test_search_navigate_next_moves_to_next_match(self, qapp, colors):
        """AC #3: search_next() moves cursor to next match."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="cat dog cat bird cat")
        panel.search_text("cat")

        # Initially at first match (0, 3)
        assert panel.get_current_match_index() == 0

        panel.search_next()
        assert panel.get_current_match_index() == 1

        panel.search_next()
        assert panel.get_current_match_index() == 2

        # Wraps around
        panel.search_next()
        assert panel.get_current_match_index() == 0

    def test_search_navigate_prev_moves_to_previous_match(self, qapp, colors):
        """AC #4: search_prev() moves cursor to previous match."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="cat dog cat bird cat")
        panel.search_text("cat")

        # Initially at first match
        assert panel.get_current_match_index() == 0

        # Previous wraps to last
        panel.search_prev()
        assert panel.get_current_match_index() == 2

        panel.search_prev()
        assert panel.get_current_match_index() == 1

    def test_search_case_sensitive_works(self, qapp, colors):
        """AC #5: case_sensitive=True finds only exact case matches."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="Apple apple APPLE ApPlE")

        # Case insensitive (default)
        matches_insensitive = panel.search_text("apple", case_sensitive=False)
        assert len(matches_insensitive) == 4

        # Case sensitive
        matches_sensitive = panel.search_text("apple", case_sensitive=True)
        assert len(matches_sensitive) == 1
        assert matches_sensitive[0] == (6, 11)  # lowercase "apple"

    def test_search_regex_works(self, qapp, colors):
        """AC #6: use_regex=True interprets pattern as regex."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="cat1 cat2 dog3 cat99")

        # Find cat followed by any digits
        matches = panel.search_text(r"cat\d+", use_regex=True)

        assert len(matches) == 3
        # cat1, cat2, cat99

    def test_search_regex_invalid_pattern(self, qapp, colors):
        """Invalid regex returns empty matches and doesn't crash."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="Some text")

        # Invalid regex pattern
        matches = panel.search_text(r"[invalid", use_regex=True)
        assert matches == []

    def test_search_clear_removes_highlights(self, qapp, colors):
        """AC #7: clear_search() removes all search highlights."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="hello hello hello")
        panel.search_text("hello")

        assert panel.get_search_highlight_count() == 3

        panel.clear_search()

        assert panel.get_search_highlight_count() == 0
        assert panel.get_current_match_index() == -1

    def test_search_match_counter_shows_current_and_total(self, qapp, colors):
        """AC #8: get_search_status() returns (current, total) tuple."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="word word word word")
        panel.search_text("word")

        current, total = panel.get_search_status()
        assert total == 4
        assert current == 1  # 1-indexed for display

        panel.search_next()
        current, total = panel.get_search_status()
        assert current == 2
        assert total == 4

    def test_search_status_no_matches(self, qapp, colors):
        """get_search_status() returns (0, 0) when no matches."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="hello world")
        panel.search_text("xyz")

        current, total = panel.get_search_status()
        assert current == 0
        assert total == 0

    def test_search_selects_current_match(self, qapp, colors):
        """Current match is selected in text editor."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="find me here find me there")
        panel.search_text("find me")

        # First match should be selected
        selection = panel.get_selection()
        assert selection == (0, 7)  # "find me"

    def test_search_scrolls_to_match(self, qapp, colors):
        """Navigating to match scrolls it into view."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        # Long text so scroll is needed
        panel.set_document(
            "Test",
            text="match\n" + ("line\n" * 100) + "match\n" + ("line\n" * 100) + "match",
        )
        panel.search_text("match")

        # Navigate to last match
        panel.search_next()
        panel.search_next()

        # Cursor should be visible (we can't easily test scroll position)
        assert panel.get_current_match_index() == 2

    def test_search_empty_query_clears_search(self, qapp, colors):
        """Searching with empty string clears search."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="hello world")
        panel.search_text("hello")

        assert panel.get_search_highlight_count() == 1

        panel.search_text("")

        assert panel.get_search_highlight_count() == 0

    def test_search_preserves_existing_highlights(self, qapp, colors):
        """Search highlights don't interfere with code highlights."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="code segment here and more code here")

        # Apply code highlight
        panel.highlight_range(0, 12, "#FFC107")

        # Search
        panel.search_text("here")

        # Code highlight should still be tracked
        assert panel.get_highlight_count() == 1

        # Search highlights are separate
        assert panel.get_search_highlight_count() == 2

    def test_search_signal_emitted_on_results(self, qapp, colors):
        """Signal emitted when search finds results."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="find this text")
        spy = QSignalSpy(panel.search_results_changed)

        panel.search_text("this")

        assert spy.count() == 1
        # Signal carries (match_count, current_index)
        assert spy.at(0)[0] == 1  # 1 match
        assert spy.at(0)[1] == 0  # current index 0


class TestSearchToolbarIntegration:
    """Tests for search integration with toolbar."""

    def test_toolbar_search_triggers_panel_search(self, qapp, colors):
        """Typing in toolbar search box triggers search in panel."""
        from src.presentation.organisms.coding_toolbar import CodingToolbar
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        toolbar = CodingToolbar(colors=colors)
        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="searchable text content")

        # Connect toolbar signal to panel
        toolbar.search_changed.connect(lambda query: panel.search_text(query))

        # Simulate search input
        toolbar._search.setText("text")

        # Panel should have search results
        assert panel.get_search_highlight_count() == 1


class TestSearchWidget:
    """Tests for the search widget component."""

    def test_search_widget_creates(self, qapp, colors):
        """SearchWidget creates with default state."""
        from src.presentation.organisms.text_editor_panel import SearchWidget

        widget = SearchWidget(colors=colors)
        assert widget is not None
        assert widget.isVisible() is False  # Hidden by default

    def test_search_widget_shows_match_count(self, qapp, colors):
        """SearchWidget displays current/total match count."""
        from src.presentation.organisms.text_editor_panel import SearchWidget

        widget = SearchWidget(colors=colors)
        widget.set_results(current=2, total=5)

        assert "2 / 5" in widget.get_status_text()

    def test_search_widget_no_results_message(self, qapp, colors):
        """SearchWidget shows 'No results' when total is 0."""
        from src.presentation.organisms.text_editor_panel import SearchWidget

        widget = SearchWidget(colors=colors)
        widget.set_results(current=0, total=0)

        assert (
            "No results" in widget.get_status_text()
            or "0 / 0" in widget.get_status_text()
        )

    def test_search_widget_emits_signals(self, qapp, colors):
        """SearchWidget emits navigation signals."""
        from src.presentation.organisms.text_editor_panel import SearchWidget

        widget = SearchWidget(colors=colors)
        next_spy = QSignalSpy(widget.next_clicked)
        prev_spy = QSignalSpy(widget.prev_clicked)
        close_spy = QSignalSpy(widget.close_clicked)

        widget._next_btn.click()
        assert next_spy.count() == 1

        widget._prev_btn.click()
        assert prev_spy.count() == 1

        widget._close_btn.click()
        assert close_spy.count() == 1

    def test_search_widget_options(self, qapp, colors):
        """SearchWidget has case sensitive and regex options."""
        from src.presentation.organisms.text_editor_panel import SearchWidget

        widget = SearchWidget(colors=colors)

        # Default state
        assert widget.is_case_sensitive() is False
        assert widget.is_regex() is False

        # Toggle options
        widget.set_case_sensitive(True)
        assert widget.is_case_sensitive() is True

        widget.set_regex(True)
        assert widget.is_regex() is True


class TestSearchScreenshot:
    """Visual tests with screenshots."""

    def test_screenshot_search_active(self, qapp, colors, take_screenshot):
        """Screenshot of text editor with active search."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document(
            "Research Notes",
            text="""The qualitative research methodology focuses on understanding
human behavior and the reasons that govern such behavior. This approach
is particularly useful when researching social phenomena, as it allows
researchers to gain insights into the subjective experiences of participants.

Key aspects of qualitative research include:
1. Research questions that explore meaning and understanding
2. Data collection through interviews and observations
3. Analysis that identifies patterns and themes
4. Findings that provide rich, contextual understanding

The research process is iterative, allowing researchers to refine their
approach as new insights emerge from the data.""",
        )

        # Search and highlight
        panel.search_text("research")
        panel.setFixedSize(800, 500)

        take_screenshot(panel, "search_in_text_active")
