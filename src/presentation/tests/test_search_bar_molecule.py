"""
Tests for SearchBar Molecule

Tests the pure presentation behavior of the SearchBar component.
This is a molecule-level test - it tests the component in isolation.
"""

from PySide6.QtTest import QSignalSpy


class TestSearchBarMolecule:
    """Unit tests for SearchBar molecule."""

    def test_hidden_by_default(self, qapp, colors):
        """SearchBar is hidden by default."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        assert bar.isVisible() is False

    def test_set_results_displays_count(self, qapp, colors):
        """set_results() updates the status display."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        bar.set_results(current=3, total=10)

        assert "3 / 10" in bar.get_status_text()

    def test_set_results_zero_shows_no_results(self, qapp, colors):
        """set_results(0, 0) shows 'No results' message."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        bar.set_results(current=0, total=0)

        assert "No results" in bar.get_status_text()

    def test_case_sensitive_default_false(self, qapp, colors):
        """Case sensitivity is off by default."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        assert bar.is_case_sensitive() is False

    def test_regex_default_false(self, qapp, colors):
        """Regex mode is off by default."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        assert bar.is_regex() is False

    def test_set_case_sensitive(self, qapp, colors):
        """set_case_sensitive() updates state."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        bar.set_case_sensitive(True)

        assert bar.is_case_sensitive() is True

    def test_set_regex(self, qapp, colors):
        """set_regex() updates state."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        bar.set_regex(True)

        assert bar.is_regex() is True

    def test_get_set_query(self, qapp, colors):
        """get_query/set_query manage the search text."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        bar.set_query("test query")

        assert bar.get_query() == "test query"


class TestSearchBarSignals:
    """Tests for SearchBar signal emissions."""

    def test_search_changed_emits_on_text_change(self, qapp, colors):
        """search_changed signal emits when text changes."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.search_changed)

        bar.set_query("test")

        assert spy.count() == 1
        assert spy.at(0)[0] == "test"

    def test_next_clicked_emits(self, qapp, colors):
        """next_clicked signal emits when next button clicked."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.next_clicked)

        bar._next_btn.click()

        assert spy.count() == 1

    def test_prev_clicked_emits(self, qapp, colors):
        """prev_clicked signal emits when prev button clicked."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.prev_clicked)

        bar._prev_btn.click()

        assert spy.count() == 1

    def test_close_clicked_emits(self, qapp, colors):
        """close_clicked signal emits when close button clicked."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.close_clicked)

        bar._close_btn.click()

        assert spy.count() == 1

    def test_options_changed_emits_on_case_toggle(self, qapp, colors):
        """options_changed signal emits when case sensitivity toggled."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.options_changed)

        bar._case_btn.setChecked(True)

        assert spy.count() == 1

    def test_options_changed_emits_on_regex_toggle(self, qapp, colors):
        """options_changed signal emits when regex mode toggled."""
        from src.presentation.molecules.search import SearchBar

        bar = SearchBar(colors=colors)
        spy = QSignalSpy(bar.options_changed)

        bar._regex_btn.setChecked(True)

        assert spy.count() == 1


class TestBackwardCompatibility:
    """Tests for backward compatibility with SearchWidget alias."""

    def test_searchwidget_is_searchbar(self, qapp, colors):
        """SearchWidget is the same class as SearchBar."""
        from src.presentation.molecules.search import SearchBar
        from src.presentation.organisms.text_editor_panel import SearchWidget

        assert SearchWidget is SearchBar
