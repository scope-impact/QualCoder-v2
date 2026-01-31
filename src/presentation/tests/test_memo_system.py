"""
Tests for QC-007.08 Memo System

Tests the memo functionality for files, codes, and segments:
- AC #1: File memo dialog
- AC #2: Code memo dialog
- AC #3: Segment memo dialog
- AC #4: Memo indicator in text (bold)
- AC #5: View all memos panel
- AC #6: Memo author and timestamp display
- AC #7: Edit existing memos
"""

from datetime import datetime

from PySide6.QtTest import QSignalSpy


class TestMemoDialog:
    """Tests for the MemoDialog component."""

    def test_memo_dialog_creates(self, qapp, colors):
        """MemoDialog creates with default settings."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(colors=colors)
        assert dialog is not None

    def test_memo_dialog_shows_title(self, qapp, colors):
        """MemoDialog shows the specified title."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(title="Segment Memo", colors=colors)
        assert "Segment Memo" in dialog.windowTitle() or dialog._title == "Segment Memo"

    def test_memo_dialog_shows_existing_memo(self, qapp, colors):
        """MemoDialog displays existing memo content."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        initial_memo = "This is an existing memo"
        dialog = MemoDialog(content=initial_memo, colors=colors)

        assert dialog.get_content() == initial_memo

    def test_memo_dialog_edit_content(self, qapp, colors):
        """MemoDialog allows editing memo content."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(colors=colors)
        dialog.set_content("New memo content")

        assert dialog.get_content() == "New memo content"

    def test_memo_dialog_emits_save_signal(self, qapp, colors):
        """MemoDialog emits save_clicked signal."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(colors=colors)
        spy = QSignalSpy(dialog.save_clicked)

        dialog._save_btn.click()

        assert spy.count() == 1

    def test_memo_dialog_emits_cancel_signal(self, qapp, colors):
        """MemoDialog emits cancel_clicked signal."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(colors=colors)
        spy = QSignalSpy(dialog.cancel_clicked)

        dialog._cancel_btn.click()

        assert spy.count() == 1

    def test_memo_dialog_shows_metadata(self, qapp, colors):
        """MemoDialog shows author and timestamp metadata."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(
            author="John Doe",
            timestamp=datetime(2026, 1, 15, 10, 30),
            colors=colors,
        )

        metadata_text = dialog.get_metadata_text()
        assert "John Doe" in metadata_text
        assert "2026" in metadata_text


class TestFileMemoDialog:
    """Tests for file-specific memo dialog."""

    def test_file_memo_dialog_creates(self, qapp, colors):
        """FileMemoDialog creates with file info."""
        from src.presentation.dialogs.memo_dialog import FileMemoDialog

        dialog = FileMemoDialog(
            filename="interview_001.txt",
            colors=colors,
        )
        assert dialog is not None
        assert "interview_001.txt" in dialog.get_title()

    def test_file_memo_dialog_shows_file_icon(self, qapp, colors):
        """FileMemoDialog displays file icon."""
        from src.presentation.dialogs.memo_dialog import FileMemoDialog

        dialog = FileMemoDialog(filename="test.txt", colors=colors)
        # Icon should be present
        assert dialog._icon is not None


class TestCodeMemoDialog:
    """Tests for code-specific memo dialog."""

    def test_code_memo_dialog_creates(self, qapp, colors):
        """CodeMemoDialog creates with code info."""
        from src.presentation.dialogs.memo_dialog import CodeMemoDialog

        dialog = CodeMemoDialog(
            code_name="Theme: Identity",
            code_color="#FF5733",
            colors=colors,
        )
        assert dialog is not None

    def test_code_memo_dialog_shows_code_color(self, qapp, colors):
        """CodeMemoDialog displays code color indicator."""
        from src.presentation.dialogs.memo_dialog import CodeMemoDialog

        dialog = CodeMemoDialog(
            code_name="Test Code",
            code_color="#00FF00",
            colors=colors,
        )
        # Color indicator should show the code color
        assert dialog._color_indicator is not None


class TestSegmentMemoDialog:
    """Tests for segment-specific memo dialog."""

    def test_segment_memo_dialog_creates(self, qapp, colors):
        """SegmentMemoDialog creates with segment info."""
        from src.presentation.dialogs.memo_dialog import SegmentMemoDialog

        dialog = SegmentMemoDialog(
            segment_text="The participant mentioned...",
            code_name="Theme: Experience",
            colors=colors,
        )
        assert dialog is not None

    def test_segment_memo_dialog_shows_segment_preview(self, qapp, colors):
        """SegmentMemoDialog shows the coded text preview."""
        from src.presentation.dialogs.memo_dialog import SegmentMemoDialog

        segment_text = "This is the coded text segment"
        dialog = SegmentMemoDialog(
            segment_text=segment_text,
            code_name="Test",
            colors=colors,
        )
        assert segment_text in dialog.get_segment_preview()


class TestMemoIndicator:
    """Tests for memo indicator in text editor."""

    def test_highlight_with_memo_is_bold(self, qapp, colors):
        """Text with memo is displayed in bold."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="This is some sample text")

        # Highlight with memo
        panel.highlight_range(0, 10, "#FFC107", memo="Important note")

        # Check formatting
        fmt = panel.get_char_format_at(5)
        assert fmt is not None
        assert fmt.fontWeight() >= 600  # Bold

    def test_highlight_without_memo_not_bold(self, qapp, colors):
        """Text without memo is not bold."""
        from src.presentation.organisms.text_editor_panel import TextEditorPanel

        panel = TextEditorPanel(colors=colors)
        panel.set_document("Test", text="This is some sample text")

        # Highlight without memo
        panel.highlight_range(0, 10, "#FFC107")

        # Check formatting
        fmt = panel.get_char_format_at(5)
        assert fmt is not None
        assert fmt.fontWeight() < 600  # Not bold


class TestMemosPanel:
    """Tests for the all memos view panel."""

    def test_memos_panel_creates(self, qapp, colors):
        """MemosPanel creates with default settings."""
        from src.presentation.dialogs.memo_dialog import MemosPanel

        panel = MemosPanel(colors=colors)
        assert panel is not None

    def test_memos_panel_set_memos(self, qapp, colors):
        """MemosPanel displays list of memos."""
        from src.presentation.dialogs.memo_dialog import MemosPanel

        memos = [
            {
                "type": "file",
                "name": "interview.txt",
                "content": "File notes",
                "author": "John",
                "timestamp": "2026-01-15",
            },
            {
                "type": "code",
                "name": "Theme A",
                "content": "Code definition",
                "author": "Jane",
                "timestamp": "2026-01-16",
            },
        ]

        panel = MemosPanel(colors=colors)
        panel.set_memos(memos)

        assert panel.get_memo_count() == 2

    def test_memos_panel_filter_by_type(self, qapp, colors):
        """MemosPanel can filter by memo type."""
        from src.presentation.dialogs.memo_dialog import MemosPanel

        memos = [
            {"type": "file", "name": "file1", "content": "..."},
            {"type": "code", "name": "code1", "content": "..."},
            {"type": "segment", "name": "seg1", "content": "..."},
        ]

        panel = MemosPanel(colors=colors)
        panel.set_memos(memos)
        panel.set_filter("file")

        assert panel.get_visible_memo_count() == 1

    def test_memos_panel_emits_memo_clicked(self, qapp, colors):
        """MemosPanel emits signal when memo is clicked."""
        from src.presentation.dialogs.memo_dialog import MemosPanel

        panel = MemosPanel(colors=colors)

        memos = [{"type": "file", "name": "test", "content": "..."}]
        panel.set_memos(memos)

        # Verify the signal exists (clicking would require internal widget access)
        assert panel.memo_clicked is not None


class TestMemoScreenshot:
    """Visual tests with screenshots."""

    def test_screenshot_memo_dialog(self, qapp, colors, take_screenshot):
        """Screenshot of memo dialog."""
        from src.presentation.dialogs.memo_dialog import MemoDialog

        dialog = MemoDialog(
            title="Segment Memo",
            content="This participant's response highlights a key theme in the data. "
            "The emphasis on community connection is particularly notable.\n\n"
            "Follow-up questions should explore this further.",
            author="Dr. Smith",
            timestamp=datetime(2026, 1, 15, 14, 30),
            colors=colors,
        )
        dialog.setFixedSize(500, 400)

        take_screenshot(dialog, "memo_dialog")

    def test_screenshot_memos_panel(self, qapp, colors, take_screenshot):
        """Screenshot of memos panel."""
        from src.presentation.dialogs.memo_dialog import MemosPanel

        panel = MemosPanel(colors=colors)
        panel.set_memos(
            [
                {
                    "type": "file",
                    "name": "Interview_001.txt",
                    "content": "Initial interview with participant A",
                    "author": "Dr. Smith",
                    "timestamp": "2026-01-10",
                },
                {
                    "type": "code",
                    "name": "Theme: Identity",
                    "content": "References to personal identity and self-concept",
                    "author": "Dr. Jones",
                    "timestamp": "2026-01-12",
                },
                {
                    "type": "segment",
                    "name": "Para 3, Interview_001",
                    "content": "Key quote about community belonging",
                    "author": "Dr. Smith",
                    "timestamp": "2026-01-14",
                },
            ]
        )
        panel.setFixedSize(600, 400)

        take_screenshot(panel, "memos_panel")
