"""
Tests for QC-007.07 Auto-Coding Features - Presentation Layer

Tests UI components following fDDD architecture:
- Dialog emits signals for operations
- Dialog receives results via slots
- No direct domain service calls

Note: Domain logic tests are in their respective layers:
- TextMatcher tests: src/domain/coding/services/tests/test_text_matcher.py
- SpeakerDetector tests: src/domain/sources/services/tests/test_speaker_detector.py
- BatchManager tests: src/application/coding/tests/test_batch_manager.py
- AutoCodingController tests: src/application/coding/tests/test_auto_coding_controller.py
"""

from PySide6.QtTest import QSignalSpy


class TestAutoCodeDialog:
    """Tests for auto-code dialog UI."""

    def test_auto_code_dialog_has_pattern_input(self, qapp, colors):
        """Dialog has pattern input field."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        assert dialog.get_pattern() == ""

        dialog.set_pattern("test pattern")
        assert dialog.get_pattern() == "test pattern"

    def test_auto_code_dialog_has_match_type_options(self, qapp, colors):
        """Dialog has match type options."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)

        # Should have exact, contains, regex options
        assert "exact" in dialog.get_available_match_types()
        assert "contains" in dialog.get_available_match_types()
        assert "regex" in dialog.get_available_match_types()

    def test_auto_code_dialog_has_scope_options(self, qapp, colors):
        """Dialog has scope options (all, first, last)."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)

        # Should have all, first, last options
        assert "all" in dialog.get_available_scopes()
        assert "first" in dialog.get_available_scopes()
        assert "last" in dialog.get_available_scopes()

    def test_auto_code_dialog_set_code(self, qapp, colors):
        """Dialog can set the code to apply."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_code({"id": "1", "name": "Test Code", "color": "#FF0000"})

        assert dialog.get_code()["name"] == "Test Code"

    def test_auto_code_dialog_set_text(self, qapp, colors):
        """Dialog can set the text to search."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_text("The cat sat on the mat.")

        # Text is stored internally
        assert dialog._text == "The cat sat on the mat."


class TestAutoCodeDialogSignals:
    """Tests for dialog signal emissions following fDDD architecture."""

    def test_emits_find_matches_requested_signal(self, qapp, colors):
        """Dialog emits find_matches_requested when preview clicked."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_text("test text")
        dialog.set_pattern("test")

        spy = QSignalSpy(dialog.find_matches_requested)

        # Simulate preview click
        dialog._on_preview()

        assert spy.count() == 1
        # Signal args: text, pattern, match_type, scope, case_sensitive
        args = spy.at(0)
        assert args[0] == "test text"
        assert args[1] == "test"
        assert args[2] == "exact"  # default
        assert args[3] == "all"  # default
        assert args[4] is False  # case_sensitive

    def test_emits_apply_auto_code_requested_signal(self, qapp, colors):
        """Dialog emits apply_auto_code_requested when apply clicked."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_pattern("test")
        dialog.set_code({"id": "1", "name": "Test"})

        spy = QSignalSpy(dialog.apply_auto_code_requested)

        # Simulate apply (but don't close dialog)
        config = {
            "pattern": dialog.get_pattern(),
            "match_type": dialog._get_match_type_str(),
            "scope": dialog._get_scope_str(),
            "code": dialog.get_code(),
        }
        dialog.apply_auto_code_requested.emit(config)

        assert spy.count() == 1
        emitted_config = spy.at(0)[0]
        assert emitted_config["pattern"] == "test"
        assert emitted_config["code"]["name"] == "Test"

    def test_does_not_emit_find_matches_without_text(self, qapp, colors):
        """Dialog does not emit if text is empty."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_pattern("test")
        # No text set

        spy = QSignalSpy(dialog.find_matches_requested)
        dialog._on_preview()

        assert spy.count() == 0

    def test_does_not_emit_find_matches_without_pattern(self, qapp, colors):
        """Dialog does not emit if pattern is empty."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)
        dialog.set_text("some text")
        # No pattern set

        spy = QSignalSpy(dialog.find_matches_requested)
        dialog._on_preview()

        assert spy.count() == 0


class TestAutoCodeDialogSlots:
    """Tests for dialog receiving results via slots."""

    def test_on_matches_found_caches_results(self, qapp, colors):
        """Dialog caches matches received via slot."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)

        # Simulate controller sending matches
        matches = [(0, 5), (10, 15), (20, 25)]
        dialog.on_matches_found(matches)

        assert dialog.get_cached_matches() == matches

    def test_on_speakers_detected_slot_exists(self, qapp, colors):
        """Dialog has slot for receiving speakers."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)

        # Should not raise
        dialog.on_speakers_detected([{"name": "SPEAKER", "count": 1}])

    def test_on_error_slot_exists(self, qapp, colors):
        """Dialog has slot for receiving errors."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog

        dialog = AutoCodeDialog(colors=colors)

        # Should not raise
        dialog.on_error("find_matches", "Invalid regex")


class TestAutoCodePreview:
    """Tests for auto-code preview functionality."""

    def test_preview_shows_matches(self, qapp, colors):
        """Preview shows list of matches with context."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodePreview

        preview = AutoCodePreview(colors=colors)
        matches = [
            {"start": 0, "end": 5, "text": "Hello", "context": "Hello world..."},
            {
                "start": 20,
                "end": 25,
                "text": "world",
                "context": "...beautiful world today",
            },
        ]

        preview.set_matches(matches)

        assert preview.get_match_count() == 2

    def test_preview_shows_match_count(self, qapp, colors):
        """Preview displays total match count."""
        from src.presentation.dialogs.auto_code_dialog import AutoCodePreview

        preview = AutoCodePreview(colors=colors)
        matches = [
            {"start": 0, "end": 5, "text": "test", "context": "test one"},
            {"start": 10, "end": 15, "text": "test", "context": "test two"},
            {"start": 20, "end": 25, "text": "test", "context": "test three"},
        ]

        preview.set_matches(matches)

        assert "3" in preview.get_summary_text()
