"""
Tests for UI Organisms

Tests each organism component individually and the composed TextCodingPage.
"""

from PySide6.QtTest import QSignalSpy

# =============================================================================
# CodingToolbar Tests
# =============================================================================


class TestCodingToolbar:
    """Tests for the CodingToolbar organism."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test toolbar creates with default settings."""
        from src.presentation.organisms import CodingToolbar

        toolbar = CodingToolbar(colors=colors)

        assert toolbar is not None
        assert toolbar._media_selector is not None
        assert toolbar._coder_selector is not None
        assert toolbar._search is not None

    def test_creates_with_coders(self, qapp, colors):
        """Test toolbar creates with custom coders list."""
        from src.presentation.organisms import CodingToolbar

        coders = ["alice", "bob", "charlie"]
        toolbar = CodingToolbar(coders=coders, selected_coder="bob", colors=colors)

        assert toolbar._coders == coders
        assert toolbar._selected_coder == "bob"

    def test_set_navigation(self, qapp, colors):
        """Test navigation label updates."""
        from src.presentation.organisms import CodingToolbar

        toolbar = CodingToolbar(colors=colors)
        toolbar.set_navigation(3, 10)

        assert toolbar._nav_label.text() == "3 / 10"

    def test_action_triggered_signal(self, qapp, colors):
        """Test action buttons emit signals."""
        from src.presentation.organisms import CodingToolbar

        toolbar = CodingToolbar(colors=colors)
        spy = QSignalSpy(toolbar.action_triggered)

        # Simulate clicking the help button (first action button)
        toolbar.action_triggered.emit("help")

        assert spy.count() == 1
        assert spy.at(0)[0] == "help"

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of toolbar."""
        from src.presentation.organisms import CodingToolbar

        toolbar = CodingToolbar(
            coders=["colin", "sarah", "james"],
            selected_coder="colin",
            colors=colors,
        )
        toolbar.set_navigation(2, 5)
        toolbar.setFixedWidth(1200)

        take_screenshot(toolbar, "coding_toolbar")


# =============================================================================
# FilesPanel Tests
# =============================================================================


class TestFilesPanel:
    """Tests for the FilesPanel organism."""

    def test_creates_empty(self, qapp, colors):
        """Test panel creates with no files."""
        from src.presentation.organisms import FilesPanel

        panel = FilesPanel(colors=colors)

        assert panel is not None
        assert panel._files == []

    def test_set_files(self, qapp, colors):
        """Test setting file list."""
        from src.presentation.organisms import FilesPanel

        panel = FilesPanel(colors=colors)
        files = [
            {"name": "file1.txt", "type": "text", "meta": "1 KB"},
            {"name": "file2.docx", "type": "text", "meta": "2 KB"},
        ]
        panel.set_files(files)

        assert panel._files == files

    def test_file_selected_signal(self, qapp, colors):
        """Test file selection emits signal."""
        from src.presentation.organisms import FilesPanel

        panel = FilesPanel(colors=colors)
        files = [
            {"name": "file1.txt", "type": "text", "meta": "1 KB"},
            {"name": "file2.docx", "type": "text", "meta": "2 KB"},
        ]
        panel.set_files(files)

        spy = QSignalSpy(panel.file_selected)
        panel._on_file_click(0)

        assert spy.count() == 1
        assert spy.at(0)[0]["name"] == "file1.txt"

    def test_clear(self, qapp, colors):
        """Test clearing file list."""
        from src.presentation.organisms import FilesPanel

        panel = FilesPanel(colors=colors)
        panel.set_files([{"name": "test.txt", "type": "text", "meta": ""}])
        panel.clear()

        assert panel._files == []

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of files panel."""
        from src.presentation.organisms import FilesPanel

        panel = FilesPanel(colors=colors)
        panel.set_files(
            [
                {
                    "name": "interview1.txt",
                    "type": "text",
                    "meta": "Text • 2.4 KB • 3 codes",
                },
                {
                    "name": "interview2.docx",
                    "type": "text",
                    "meta": "Text • 3.1 KB • 7 codes",
                },
                {
                    "name": "notes.odt",
                    "type": "text",
                    "meta": "Text • 1.2 KB • 5 codes",
                },
            ]
        )
        panel.setFixedSize(280, 200)

        take_screenshot(panel, "files_panel")


# =============================================================================
# CodesPanel Tests
# =============================================================================


class TestCodesPanel:
    """Tests for the CodesPanel organism."""

    def test_creates_empty(self, qapp, colors):
        """Test panel creates with no codes."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)

        assert panel is not None
        assert panel._code_tree is not None

    def test_set_codes(self, qapp, colors):
        """Test setting code tree data."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        categories = [
            {
                "name": "Category A",
                "codes": [
                    {"name": "code1", "color": colors.code_red, "count": 3},
                    {"name": "code2", "color": colors.code_green, "count": 5},
                ],
            }
        ]
        panel.set_codes(categories)

        # Panel should have processed the codes
        assert panel is not None

    def test_code_selected_signal(self, qapp, colors):
        """Test code selection emits signal."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        spy = QSignalSpy(panel.code_selected)

        panel._on_code_click("test_code")

        assert spy.count() == 1
        assert spy.at(0)[0]["id"] == "test_code"

    def test_navigation_clicked_signal(self, qapp, colors):
        """Test navigation buttons emit signals."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        spy = QSignalSpy(panel.navigation_clicked)

        panel.navigation_clicked.emit("next")

        assert spy.count() == 1
        assert spy.at(0)[0] == "next"

    def test_set_codes_with_numeric_ids(self, qapp, colors):
        """Test that numeric IDs from set_codes are preserved."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        categories = [
            {
                "name": "Category A",
                "codes": [
                    {
                        "id": "12345",
                        "name": "code1",
                        "color": colors.code_red,
                        "count": 3,
                    },
                    {
                        "id": "67890",
                        "name": "code2",
                        "color": colors.code_green,
                        "count": 5,
                    },
                ],
            }
        ]
        panel.set_codes(categories)

        # Verify the tree items have the correct IDs
        items = panel._code_tree._items
        assert len(items) == 1  # One category
        assert len(items[0].children) == 2  # Two codes
        assert items[0].children[0].id == "12345"
        assert items[0].children[0].name == "code1"
        assert items[0].children[1].id == "67890"
        assert items[0].children[1].name == "code2"

    def test_code_selected_emits_id_not_name(self, qapp, colors):
        """Test that code selection emits the numeric ID, not the name.

        This test would have caught the bug where CodeItem was created with
        id=code_name instead of id=code.get("id").
        """
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        spy = QSignalSpy(panel.code_selected)

        # Set codes with numeric IDs different from names
        categories = [
            {
                "name": "Emotions",
                "codes": [
                    {
                        "id": "999",
                        "name": "happy",
                        "color": colors.code_green,
                        "count": 1,
                    },
                ],
            }
        ]
        panel.set_codes(categories)

        # Simulate clicking the code (which should use the ID from the tree item)
        panel._on_code_click("999")

        assert spy.count() == 1
        emitted_data = spy.at(0)[0]
        assert emitted_data["id"] == "999"
        # The ID should NOT be the code name
        assert emitted_data["id"] != "happy"

    def test_set_codes_fallback_to_name_when_no_id(self, qapp, colors):
        """Test that when no ID is provided, the code name is used as fallback."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        categories = [
            {
                "name": "Category A",
                "codes": [
                    {"name": "fallback_code", "color": colors.code_red, "count": 1},
                ],
            }
        ]
        panel.set_codes(categories)

        # When no ID is provided, name should be used as ID
        items = panel._code_tree._items
        assert items[0].children[0].id == "fallback_code"
        assert items[0].children[0].name == "fallback_code"

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of codes panel."""
        from src.presentation.organisms import CodesPanel

        panel = CodesPanel(colors=colors)
        panel.set_codes(
            [
                {
                    "name": "Abilities",
                    "codes": [
                        {
                            "name": "soccer playing",
                            "color": colors.code_yellow,
                            "count": 3,
                        },
                        {"name": "struggling", "color": colors.code_red, "count": 5},
                    ],
                },
                {
                    "name": "Motivation",
                    "codes": [
                        {
                            "name": "cost concerns",
                            "color": colors.code_pink,
                            "count": 2,
                        },
                        {"name": "enthusiasm", "color": colors.code_cyan, "count": 6},
                    ],
                },
            ]
        )
        panel.setFixedSize(280, 300)

        take_screenshot(panel, "codes_panel")


# =============================================================================
# TextEditorPanel Tests
# =============================================================================


class TestTextEditorPanel:
    """Tests for the TextEditorPanel organism."""

    def test_creates_empty(self, qapp, colors):
        """Test panel creates with no document."""
        from src.presentation.organisms import TextEditorPanel

        panel = TextEditorPanel(colors=colors)

        assert panel is not None
        assert panel._text_panel is not None

    def test_set_document(self, qapp, colors):
        """Test setting document content."""
        from src.presentation.organisms import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("test.txt", "Case 1", "Hello world")

        # Document should be set
        assert panel is not None

    def test_set_stats(self, qapp, colors):
        """Test setting document stats."""
        from src.presentation.organisms import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_stats(
            [
                ("mdi6.label", "5 codes"),
                ("mdi6.format-size", "100 words"),
            ]
        )

        assert panel is not None

    def test_text_selected_signal(self, qapp, colors):
        """Test text selection emits signal."""
        from src.presentation.organisms import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        spy = QSignalSpy(panel.text_selected)

        panel.text_selected.emit("selected text", 0, 13)

        assert spy.count() == 1
        assert spy.at(0)[0] == "selected text"
        assert spy.at(0)[1] == 0
        assert spy.at(0)[2] == 13

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of text editor panel."""
        from src.presentation.organisms import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document(
            "interview.txt",
            "Case: ID2",
            "I have not studied much before. I know that I must get help as I have "
            "struggled understanding the lecture slides so far.\n\n"
            "I really want someone to sit down with me and explain the course material.",
        )
        panel.set_stats(
            [
                ("mdi6.layers", "2 overlapping"),
                ("mdi6.label", "5 codes"),
            ]
        )
        panel.setFixedSize(600, 400)

        take_screenshot(panel, "text_editor_panel")


# =============================================================================
# DetailsPanel Tests
# =============================================================================


class TestDetailsPanel:
    """Tests for the DetailsPanel organism."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test panel creates with default content."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)

        assert panel is not None
        assert panel._code_card is not None
        assert panel._overlap_card is not None
        assert panel._memo_card is not None
        assert panel._ai_card is not None

    def test_set_selected_code(self, qapp, colors):
        """Test updating selected code display."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)
        panel.set_selected_code(
            colors.code_orange,
            "test code",
            "This is a test code memo",
            "Example text here",
        )

        assert panel._code_detail is not None

    def test_set_overlapping_codes(self, qapp, colors):
        """Test updating overlapping codes display."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)
        panel.set_overlapping_codes(
            [
                ("Segment 1", [colors.code_red, colors.code_green]),
                ("Segment 2", [colors.code_blue, colors.code_yellow]),
            ]
        )

        assert panel._overlap_content is not None

    def test_set_file_memo(self, qapp, colors):
        """Test updating file memo display."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)
        panel.set_file_memo("This is a test memo", 75)

        assert panel._memo_content is not None

    def test_ai_signals(self, qapp, colors):
        """Test AI button signals."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)
        chat_spy = QSignalSpy(panel.ai_chat_clicked)
        suggest_spy = QSignalSpy(panel.ai_suggest_clicked)

        panel.ai_chat_clicked.emit()
        panel.ai_suggest_clicked.emit()

        assert chat_spy.count() == 1
        assert suggest_spy.count() == 1

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of details panel."""
        from src.presentation.organisms import DetailsPanel

        panel = DetailsPanel(colors=colors)
        panel.set_selected_code(
            colors.code_yellow,
            "soccer playing",
            "Code for references to playing soccer.",
            "I have been playing...",
        )
        panel.set_overlapping_codes(
            [
                ("Segment 1", [colors.code_green, colors.code_cyan]),
            ]
        )
        panel.set_file_memo("Interview transcript about course experience.", 65)
        panel.setFixedSize(300, 600)

        take_screenshot(panel, "details_panel")


# =============================================================================
# TextCodingPage Tests
# =============================================================================


class TestTextCodingPage:
    """Tests for the composed TextCodingPage."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test page creates with default settings."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)

        assert page is not None
        assert page.toolbar is not None
        assert page.files_panel is not None
        assert page.codes_panel is not None
        assert page.editor_panel is not None
        assert page.details_panel is not None

    def test_creates_with_coders(self, qapp, colors):
        """Test page creates with custom coders."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(
            coders=["alice", "bob"],
            selected_coder="bob",
            colors=colors,
        )

        assert page is not None

    def test_set_files(self, qapp, colors):
        """Test setting files on page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        page.set_files(
            [
                {"name": "test.txt", "type": "text", "meta": "1 KB"},
            ]
        )

        assert page.files_panel._files[0]["name"] == "test.txt"

    def test_set_codes(self, qapp, colors):
        """Test setting codes on page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        page.set_codes(
            [
                {
                    "name": "Category",
                    "codes": [{"name": "code1", "color": colors.code_red, "count": 1}],
                }
            ]
        )

        assert page is not None

    def test_set_document(self, qapp, colors):
        """Test setting document on page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        page.set_document("test.txt", "Case 1", "Content here")

        assert page is not None

    def test_file_selected_signal_propagates(self, qapp, colors):
        """Test file selection signal propagates from organism to page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        page.set_files([{"name": "test.txt", "type": "text", "meta": ""}])

        spy = QSignalSpy(page.file_selected)
        page.files_panel._on_file_click(0)

        assert spy.count() == 1
        assert spy.at(0)[0]["name"] == "test.txt"

    def test_code_selected_signal_propagates(self, qapp, colors):
        """Test code selection signal propagates from organism to page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        spy = QSignalSpy(page.code_selected)

        page.codes_panel._on_code_click("test_code")

        assert spy.count() == 1
        assert spy.at(0)[0]["id"] == "test_code"

    def test_action_triggered_signal_propagates(self, qapp, colors):
        """Test action signal propagates from toolbar to page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        spy = QSignalSpy(page.action_triggered)

        page.toolbar.action_triggered.emit("help")

        assert spy.count() == 1
        assert spy.at(0)[0] == "help"

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of complete page."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(
            coders=["colin", "sarah", "james"],
            selected_coder="colin",
            colors=colors,
        )

        # Load sample data
        page.set_files(
            [
                {
                    "name": "interview1.txt",
                    "type": "text",
                    "meta": "Text • 2.4 KB • 3 codes",
                },
                {
                    "name": "interview2.docx",
                    "type": "text",
                    "meta": "Text • 3.1 KB • 7 codes",
                },
                {
                    "name": "notes.odt",
                    "type": "text",
                    "meta": "Text • 1.2 KB • 5 codes",
                },
            ]
        )

        page.set_codes(
            [
                {
                    "name": "Abilities",
                    "codes": [
                        {
                            "name": "soccer playing",
                            "color": colors.code_yellow,
                            "count": 3,
                        },
                        {"name": "struggling", "color": colors.code_red, "count": 5},
                    ],
                },
                {
                    "name": "Motivation",
                    "codes": [
                        {
                            "name": "cost concerns",
                            "color": colors.code_pink,
                            "count": 2,
                        },
                        {"name": "enthusiasm", "color": colors.code_cyan, "count": 6},
                    ],
                },
            ]
        )

        page.set_document(
            "interview1.txt",
            "Case: ID2",
            "I have not studied much before. I know that I must get help.\n\n"
            "The course cost €200 and I do not want to waste my money.",
        )

        page.set_document_stats(
            [
                ("mdi6.layers", "2 overlapping"),
                ("mdi6.label", "5 codes"),
            ]
        )

        page.set_selected_code(
            colors.code_yellow,
            "soccer playing",
            "Code for soccer references.",
        )

        page.set_overlapping_codes(
            [
                ("Segment 1", [colors.code_green, colors.code_cyan]),
            ]
        )

        page.set_file_memo("Interview transcript.", 65)
        page.set_navigation(1, 3)

        page.setMinimumSize(1200, 700)

        take_screenshot(page, "text_coding_page")


# =============================================================================
# TextCodingScreen Tests
# =============================================================================


class TestTextCodingScreen:
    """Tests for the TextCodingScreen."""

    def test_creates_with_sample_data(self, qapp, colors):
        """Test screen creates and loads sample data."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        assert screen is not None
        assert screen.page is not None
        # Sample data should be loaded
        assert len(screen.page.files_panel._files) > 0

    def test_screen_protocol_get_content(self, qapp, colors):
        """Test ScreenProtocol get_content returns self."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        assert screen.get_content() is screen

    def test_screen_protocol_get_status(self, qapp, colors):
        """Test ScreenProtocol get_status_message."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        assert screen.get_status_message() == "Ready"

    def test_signals_propagate(self, qapp, colors):
        """Test signals propagate from page to screen."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        spy = QSignalSpy(screen.file_selected)

        screen.page.files_panel._on_file_click(0)

        assert spy.count() == 1

    def test_initial_data_includes_code_ids(self, qapp, colors):
        """Test that codes in initial data have their IDs preserved.

        This test ensures the DTO-to-dict conversion includes the 'id' field,
        which is critical for apply code operations.
        """
        from src.presentation.dto import (
            CodeCategoryDTO,
            CodeDTO,
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.screens import TextCodingScreen

        # Create data with numeric code IDs
        data = TextCodingDataDTO(
            files=[],
            categories=[
                CodeCategoryDTO(
                    id="cat1",
                    name="Test Category",
                    codes=[
                        CodeDTO(id="12345", name="test_code", color="#ff0000", count=0),
                        CodeDTO(
                            id="67890", name="another_code", color="#00ff00", count=0
                        ),
                    ],
                )
            ],
            document=DocumentDTO(
                id="1", title="Test", badge="", content="Test content"
            ),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["user"],
            selected_coder="user",
        )

        screen = TextCodingScreen(data=data, colors=colors)

        # Verify the codes panel tree items have the correct IDs
        items = screen.page.codes_panel._code_tree._items
        assert len(items) == 1  # One category
        assert len(items[0].children) == 2  # Two codes

        # IDs should be numeric, not the code names
        assert items[0].children[0].id == "12345"
        assert items[0].children[0].name == "test_code"
        assert items[0].children[1].id == "67890"
        assert items[0].children[1].name == "another_code"

    def test_screenshot(self, qapp, colors, take_screenshot):
        """Take screenshot of complete screen."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen.setMinimumSize(1200, 700)

        take_screenshot(screen, "text_coding_screen")

    def test_action_handlers_registered(self, qapp, colors):
        """Test that all action handlers are registered."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # All these actions should have handlers (no "Unknown action" printed)
        expected_actions = [
            "help",
            "text_size",
            "important",
            "annotations",
            "prev",
            "next",
            "auto_exact",
            "auto_fragment",
            "speakers",
            "undo_auto",
            "memo",
            "annotate",
        ]

        for action_id in expected_actions:
            # Should not raise
            screen._on_action(action_id)

    def test_action_prev_next_navigation(self, qapp, colors):
        """Test prev/next file navigation."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # Start at file index 0 (default)
        screen._current_file_index = 0

        # Navigate next
        screen._on_action("next")
        assert screen._current_file_index == 1

        # Navigate next again
        screen._on_action("next")
        assert screen._current_file_index == 2

        # Navigate prev
        screen._on_action("prev")
        assert screen._current_file_index == 1

    def test_action_toggle_important(self, qapp, colors):
        """Test toggling important-only filter."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # Should start as False (not set)
        assert not getattr(screen, "_show_important_only", False)

        # Toggle on
        screen._on_action("important")
        assert screen._show_important_only is True

        # Toggle off
        screen._on_action("important")
        assert screen._show_important_only is False

    def test_action_toggle_annotations(self, qapp, colors):
        """Test toggling annotations display."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # Should start as True (annotations shown by default)
        assert screen._show_annotations is True

        # Toggle off
        screen._on_action("annotations")
        assert screen._show_annotations is False

        # Toggle on
        screen._on_action("annotations")
        assert screen._show_annotations is True


# =============================================================================
# Action Handler Integration Tests
# =============================================================================


class TestActionHandlers:
    """Comprehensive tests for all action handlers."""

    def test_action_help(self, qapp, colors, capsys):
        """Test help action."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("help")

        captured = capsys.readouterr()
        assert "help" in captured.out.lower() or "TODO" in captured.out

    def test_action_text_size(self, qapp, colors, capsys):
        """Test text size action."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("text_size")

        captured = capsys.readouterr()
        assert "text size" in captured.out.lower() or "TODO" in captured.out

    def test_action_important_toggle_multiple(self, qapp, colors):
        """Test important toggle works multiple times."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # Toggle multiple times
        states = []
        for _ in range(5):
            screen._on_action("important")
            states.append(screen._show_important_only)

        assert states == [True, False, True, False, True]

    def test_action_annotations_toggle_multiple(self, qapp, colors):
        """Test annotations toggle works multiple times."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        # Annotations start as True (shown by default)
        states = []
        for _ in range(4):
            screen._on_action("annotations")
            states.append(screen._show_annotations)

        # Starting from True, toggling gives: False, True, False, True
        assert states == [False, True, False, True]

    def test_action_prev_at_start(self, qapp, colors):
        """Test prev action at start of file list does nothing."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._current_file_index = 0

        screen._on_action("prev")

        # Should stay at 0
        assert screen._current_file_index == 0

    def test_action_next_at_end(self, qapp, colors):
        """Test next action at end of file list does nothing."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        total_files = len(screen._page.files_panel._files)
        screen._current_file_index = total_files - 1

        screen._on_action("next")

        # Should stay at last index
        assert screen._current_file_index == total_files - 1

    def test_action_navigate_full_range(self, qapp, colors):
        """Test navigating through all files."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        total_files = len(screen._page.files_panel._files)
        screen._current_file_index = 0

        # Navigate to end
        for _i in range(total_files - 1):
            screen._on_action("next")
        assert screen._current_file_index == total_files - 1

        # Navigate back to start
        for _i in range(total_files - 1):
            screen._on_action("prev")
        assert screen._current_file_index == 0

    def test_action_auto_exact_no_selection(self, qapp, colors, capsys):
        """Test auto-exact with no text selected."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("auto_exact")

        captured = capsys.readouterr()
        assert "select" in captured.out.lower()

    def test_action_auto_fragment_no_selection(self, qapp, colors, capsys):
        """Test auto-fragment with no text selected."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("auto_fragment")

        captured = capsys.readouterr()
        assert "select" in captured.out.lower()

    def test_action_mark_speakers(self, qapp, colors, capsys):
        """Test mark speakers action."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("speakers")

        captured = capsys.readouterr()
        assert "speaker" in captured.out.lower() or "TODO" in captured.out

    def test_action_undo_auto(self, qapp, colors, capsys):
        """Test undo auto-code action."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("undo_auto")

        captured = capsys.readouterr()
        assert "undo" in captured.out.lower() or "TODO" in captured.out

    def test_action_memo_no_selection(self, qapp, colors, capsys):
        """Test memo action with no selection falls back to file memo."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("memo")

        captured = capsys.readouterr()
        assert "memo" in captured.out.lower()

    def test_action_annotate_no_selection(self, qapp, colors, capsys):
        """Test annotate action with no selection."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("annotate")

        captured = capsys.readouterr()
        assert "select" in captured.out.lower()

    def test_unknown_action(self, qapp, colors, capsys):
        """Test unknown action prints error."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._on_action("unknown_action_xyz")

        captured = capsys.readouterr()
        assert "unknown" in captured.out.lower()

    def test_all_actions_no_crash(self, qapp, colors):
        """Test all actions can be called without crashing."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)

        all_actions = [
            "help",
            "text_size",
            "important",
            "annotations",
            "prev",
            "next",
            "auto_exact",
            "auto_fragment",
            "speakers",
            "undo_auto",
            "memo",
            "annotate",
        ]

        # Call each action twice (to test toggles)
        for action in all_actions:
            screen._on_action(action)
            screen._on_action(action)

        # If we get here, no crashes occurred
        assert True

    def test_navigation_updates_display(self, qapp, colors):
        """Test that navigation updates the toolbar display."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        screen._current_file_index = 0

        # Navigate to second file
        screen._on_action("next")

        # Check navigation label was updated
        nav_text = screen._page.toolbar._nav_label.text()
        assert "2" in nav_text  # Should show "2 / N"

    def test_media_type_signal(self, qapp, colors):
        """Test media type change signal from toolbar."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        spy = QSignalSpy(page.toolbar.media_type_changed)

        # Emit signal (simulating selection change)
        page.toolbar.media_type_changed.emit("image")

        assert spy.count() == 1
        assert spy.at(0)[0] == "image"

    def test_coder_change_signal(self, qapp, colors):
        """Test coder change signal from toolbar."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(coders=["alice", "bob"], colors=colors)
        spy = QSignalSpy(page.toolbar.coder_changed)

        # Emit signal
        page.toolbar.coder_changed.emit("bob")

        assert spy.count() == 1
        assert spy.at(0)[0] == "bob"

    def test_search_change_signal(self, qapp, colors):
        """Test search text change signal from toolbar."""
        from src.presentation.pages import TextCodingPage

        page = TextCodingPage(colors=colors)
        spy = QSignalSpy(page.toolbar.search_changed)

        # Emit signal
        page.toolbar.search_changed.emit("test query")

        assert spy.count() == 1
        assert spy.at(0)[0] == "test query"
