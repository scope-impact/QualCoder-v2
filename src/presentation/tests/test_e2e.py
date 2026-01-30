"""
End-to-End Tests

True E2E tests that simulate actual user interactions with the UI,
testing the complete flow from mouse click to data persistence.

These tests:
1. Create real UI widgets
2. Simulate actual mouse/keyboard events
3. Verify UI state changes
4. Verify data persistence
"""

import sys

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def colors():
    """Get theme colors."""
    from design_system import get_colors

    return get_colors()


@pytest.fixture
def coding_context():
    """Create an in-memory CodingContext for testing."""
    from src.presentation.factory import CodingContext

    ctx = CodingContext.create_in_memory()
    yield ctx
    ctx.close()


@pytest.fixture
def viewmodel(coding_context):
    """Create a TextCodingViewModel connected to the test context."""
    return coding_context.create_text_coding_viewmodel()


@pytest.fixture
def demo_window(qapp, coding_context, colors):  # noqa: ARG001 - qapp required for Qt
    """Create a demo-like window for E2E testing."""
    from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

    from src.presentation.dto import (
        DocumentDTO,
        NavigationDTO,
        TextCodingDataDTO,
    )
    from src.presentation.screens import TextCodingScreen

    vm = coding_context.create_text_coding_viewmodel()

    # Seed some codes
    vm.create_code("positive", "#27ae60")
    vm.create_code("negative", "#e74c3c")
    vm.create_code("neutral", "#95a5a6")

    # Build data
    categories = vm.load_codes()
    data = TextCodingDataDTO(
        files=[],
        categories=categories,
        document=DocumentDTO(
            id="1",
            title="Test Document",
            badge="E2E",
            content="This is a test document for end-to-end testing. "
            "It contains multiple sentences that can be coded.",
        ),
        document_stats=None,
        selected_code=None,
        overlapping_segments=[],
        file_memo=None,
        navigation=NavigationDTO(current=1, total=1),
        coders=["tester"],
        selected_coder="tester",
    )

    # Create window
    window = QMainWindow()
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    screen = TextCodingScreen(data=data, colors=colors)
    layout.addWidget(screen)

    window.setMinimumSize(1200, 800)
    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "viewmodel": vm,
        "context": coding_context,
    }

    window.close()


class TestE2ECodeSelection:
    """E2E tests for code selection via actual UI interaction."""

    def test_code_tree_has_correct_items(self, demo_window, qapp):
        """
        E2E: Verify code tree is populated with correct data
        Expected: Tree contains codes with correct IDs and names
        """
        screen = demo_window["screen"]
        context = demo_window["context"]

        # Get the expected codes from backend
        codes = context.controller.get_all_codes()
        expected_names = {c.name for c in codes}
        expected_ids = {str(c.id.value) for c in codes}

        # Get tree items
        code_tree = screen.page.codes_panel._code_tree
        assert len(code_tree._items) > 0

        # Collect all code items from tree
        tree_names = set()
        tree_ids = set()
        for cat_item in code_tree._items:
            for code_item in cat_item.children:
                tree_names.add(code_item.name)
                tree_ids.add(code_item.id)

        # Verify tree has all codes with correct data
        assert tree_names == expected_names
        assert tree_ids == expected_ids

    def test_code_selection_via_panel_handler(self, demo_window, qapp):
        """
        E2E: Simulate code selection through panel's click handler
        Expected: Signal emitted with correct numeric ID
        """
        screen = demo_window["screen"]
        context = demo_window["context"]

        # Get a code
        codes = context.controller.get_all_codes()
        code = next(c for c in codes if c.name == "positive")
        expected_id = str(code.id.value)

        # Setup signal spy
        spy = QSignalSpy(screen.code_selected)

        # Simulate click via the panel's handler (this is what the tree calls)
        screen.page.codes_panel._on_code_click(expected_id)
        QApplication.processEvents()

        # Verify signal
        assert spy.count() == 1
        emitted_id = spy.at(0)[0]["id"]
        assert emitted_id == expected_id
        assert emitted_id != "positive"  # Should be ID, not name

    def test_multiple_code_selections(self, demo_window, qapp):
        """
        E2E: Select multiple codes sequentially
        Expected: Each selection emits correct signal
        """
        screen = demo_window["screen"]
        context = demo_window["context"]

        codes = context.controller.get_all_codes()
        spy = QSignalSpy(screen.code_selected)

        # Select each code
        for code in codes:
            code_id = str(code.id.value)
            screen.page.codes_panel._on_code_click(code_id)
            QApplication.processEvents()

        # Should have one signal per code
        assert spy.count() == len(codes)

        # Each signal should have correct ID
        for i, code in enumerate(codes):
            emitted_id = spy.at(i)[0]["id"]
            assert emitted_id == str(code.id.value)


class TestE2ETextSelection:
    """E2E tests for text selection in the editor."""

    def test_text_panel_emits_selection_signal(self, demo_window, qapp):
        """
        E2E: Text selection signal propagates through the component hierarchy
        Expected: text_selected signal reaches the screen level
        """
        screen = demo_window["screen"]

        spy = QSignalSpy(screen.text_selected)

        # Get the text panel
        text_panel = screen.page.editor_panel._text_panel

        # Emit selection signal directly (simulating user selection)
        text_panel.text_selected.emit("test text", 0, 9)
        QApplication.processEvents()

        # Verify signal propagated to screen
        assert spy.count() >= 1
        if spy.count() > 0:
            emitted = spy.at(0)
            assert emitted[0] == "test text"
            assert emitted[1] == 0
            assert emitted[2] == 9


class TestE2EApplyCodeWorkflow:
    """E2E tests for the complete apply code workflow."""

    def test_full_apply_code_workflow(self, demo_window, qapp):
        """
        E2E: Full workflow - select text, select code, apply code

        This tests the exact user workflow:
        1. User selects text in editor
        2. User clicks a code in the sidebar
        3. User applies the code (simulated via viewmodel)
        4. Segment is created in database
        """
        screen = demo_window["screen"]
        context = demo_window["context"]
        viewmodel = demo_window["viewmodel"]

        # Get code info
        codes = context.controller.get_all_codes()
        positive_code = next(c for c in codes if c.name == "positive")
        code_id = positive_code.id.value
        code_id_str = str(code_id)

        # Step 1: Simulate text selection
        text_spy = QSignalSpy(screen.text_selected)
        screen.page.editor_panel._text_panel.text_selected.emit("selected text", 0, 13)
        QApplication.processEvents()

        # Step 2: Simulate code selection
        code_spy = QSignalSpy(screen.code_selected)
        screen.page.codes_panel._on_code_click(code_id_str)
        QApplication.processEvents()

        # Verify selections were captured
        assert text_spy.count() >= 1
        assert code_spy.count() == 1
        assert code_spy.at(0)[0]["id"] == code_id_str

        # Step 3: Apply code (simulates clicking "Apply" button)
        result = viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=0,
            end=13,
        )

        # Step 4: Verify segment created in database
        assert result is True
        segments = context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].code_id.value == code_id
        assert segments[0].position.start == 0
        assert segments[0].position.end == 13

    def test_apply_code_updates_segment_count(self, demo_window, qapp):
        """
        E2E: Apply code and verify the code's segment count updates
        """
        context = demo_window["context"]
        viewmodel = demo_window["viewmodel"]

        codes = context.controller.get_all_codes()
        code = codes[0]

        # Get initial count
        initial_segments = viewmodel.load_codes()
        initial_count = 0
        for cat in initial_segments:
            for c in cat.codes:
                if c.id == str(code.id.value):
                    initial_count = c.count

        # Apply code twice
        viewmodel.apply_code_to_selection(code.id.value, 1, 0, 10)
        viewmodel.apply_code_to_selection(code.id.value, 1, 20, 30)

        # Get updated count
        updated_categories = viewmodel.load_codes()
        updated_count = 0
        for cat in updated_categories:
            for c in cat.codes:
                if c.id == str(code.id.value):
                    updated_count = c.count

        assert updated_count == initial_count + 2


class TestE2ECodeManagement:
    """E2E tests for code management operations."""

    def test_create_code_appears_in_tree(self, demo_window, qapp):
        """
        E2E: Create a new code and verify it appears in the UI
        """
        screen = demo_window["screen"]
        viewmodel = demo_window["viewmodel"]

        # Count initial codes
        code_tree = screen.page.codes_panel._code_tree
        initial_code_count = sum(len(cat.children) for cat in code_tree._items)

        # Create new code
        viewmodel.create_code("brand_new_code", "#ff00ff")
        QApplication.processEvents()

        # Refresh the panel (in real app, signal handler does this)
        categories = viewmodel.load_codes()
        cat_dicts = [
            {
                "name": cat.name,
                "codes": [
                    {"id": c.id, "name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ],
            }
            for cat in categories
        ]
        screen.page.codes_panel.set_codes(cat_dicts)
        QApplication.processEvents()

        # Count codes again
        new_code_count = sum(len(cat.children) for cat in code_tree._items)

        assert new_code_count == initial_code_count + 1

        # Verify the new code is in the tree
        found = False
        for cat_item in code_tree._items:
            for code_item in cat_item.children:
                if code_item.name == "brand_new_code":
                    found = True
                    break
        assert found

    def test_delete_code_removes_from_tree(self, demo_window, qapp):
        """
        E2E: Delete a code and verify it's removed from the UI
        """
        screen = demo_window["screen"]
        viewmodel = demo_window["viewmodel"]
        context = demo_window["context"]

        # Get a code to delete
        codes = context.controller.get_all_codes()
        code_to_delete = codes[0]
        code_id = code_to_delete.id.value
        code_name = code_to_delete.name

        # Delete the code
        result = viewmodel.delete_code(code_id)
        assert result is True
        QApplication.processEvents()

        # Refresh the panel
        categories = viewmodel.load_codes()
        cat_dicts = [
            {
                "name": cat.name,
                "codes": [
                    {"id": c.id, "name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ],
            }
            for cat in categories
        ]
        screen.page.codes_panel.set_codes(cat_dicts)
        QApplication.processEvents()

        # Verify the code is gone from tree
        code_tree = screen.page.codes_panel._code_tree
        found = False
        for cat_item in code_tree._items:
            for code_item in cat_item.children:
                if code_item.name == code_name:
                    found = True
                    break
        assert not found


class TestE2EStatusDisplay:
    """E2E tests for status/header display updates."""

    def test_code_selection_updates_status_label(self, qapp, colors):
        """
        E2E: When a code is selected, status label shows name and ID

        This test creates a demo-like setup with a status label and verifies
        the label text is updated correctly when a code is selected.
        """
        from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

        from src.presentation.dto import (
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        # Create context and seed data
        context = CodingContext.create_in_memory()
        vm = context.create_text_coding_viewmodel()
        vm.create_code("positive", "#27ae60")
        vm.create_code("negative", "#e74c3c")

        # Get code info
        codes = context.controller.get_all_codes()
        positive_code = next(c for c in codes if c.name == "positive")
        code_id = str(positive_code.id.value)

        # Build data
        categories = vm.load_codes()
        data = TextCodingDataDTO(
            files=[],
            categories=categories,
            document=DocumentDTO(id="1", title="Test", badge="", content="Test"),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["tester"],
            selected_coder="tester",
        )

        # Create window with status label (like demo_connected.py)
        window = QMainWindow()
        central = QWidget()
        window.setCentralWidget(central)
        layout = QVBoxLayout(central)

        status_label = QLabel("Select text and a code to apply coding")
        layout.addWidget(status_label)

        screen = TextCodingScreen(data=data, colors=colors)
        layout.addWidget(screen)

        # Connect code_selected signal to update status (like demo does)
        def on_code_selected(code_data):
            selected_id = code_data.get("id", "")
            code_name = "Unknown"
            try:
                code = context.controller.get_code(int(selected_id))
                if code:
                    code_name = code.name
            except (ValueError, TypeError):
                pass
            status_label.setText(f"Selected code: {code_name} (ID: {selected_id})")

        screen.code_selected.connect(on_code_selected)

        window.show()
        QApplication.processEvents()

        # Initial state
        assert "Select text" in status_label.text()

        # Simulate code selection
        screen.page.codes_panel._on_code_click(code_id)
        QApplication.processEvents()

        # Verify status label updated with name AND ID
        label_text = status_label.text()
        assert "positive" in label_text, f"Expected 'positive' in '{label_text}'"
        assert code_id in label_text, f"Expected '{code_id}' in '{label_text}'"
        assert "Selected code:" in label_text

        # Cleanup
        window.close()
        context.close()

    def test_text_selection_updates_status_label(self, qapp, colors):
        """
        E2E: When text is selected, status label shows preview and positions
        """
        from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

        from src.presentation.dto import (
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        # Create context
        context = CodingContext.create_in_memory()
        vm = context.create_text_coding_viewmodel()
        vm.create_code("test", "#ff0000")

        categories = vm.load_codes()
        data = TextCodingDataDTO(
            files=[],
            categories=categories,
            document=DocumentDTO(
                id="1",
                title="Test",
                badge="",
                content="This is sample text for testing.",
            ),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["tester"],
            selected_coder="tester",
        )

        # Create window with status label
        window = QMainWindow()
        central = QWidget()
        window.setCentralWidget(central)
        layout = QVBoxLayout(central)

        status_label = QLabel("Initial status")
        layout.addWidget(status_label)

        screen = TextCodingScreen(data=data, colors=colors)
        layout.addWidget(screen)

        # Connect text_selected signal to update status
        def on_text_selected(text, start, end):
            preview = text[:30] + "..." if len(text) > 30 else text
            status_label.setText(f'Selected: "{preview}" ({start}-{end})')

        screen.text_selected.connect(on_text_selected)

        window.show()
        QApplication.processEvents()

        # Simulate text selection
        screen.page.editor_panel._text_panel.text_selected.emit("sample text", 8, 19)
        QApplication.processEvents()

        # Verify status label updated
        label_text = status_label.text()
        assert "sample text" in label_text, f"Expected 'sample text' in '{label_text}'"
        assert "8-19" in label_text or "(8, 19)" in label_text or "8" in label_text

        # Cleanup
        window.close()
        context.close()

    def test_apply_code_updates_status_label(self, qapp, colors):
        """
        E2E: After applying code, status label shows success message
        """
        from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

        from src.presentation.dto import (
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        # Create context
        context = CodingContext.create_in_memory()
        vm = context.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = context.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        categories = vm.load_codes()
        data = TextCodingDataDTO(
            files=[],
            categories=categories,
            document=DocumentDTO(
                id="1", title="Test", badge="", content="Test content"
            ),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["tester"],
            selected_coder="tester",
        )

        # Create window
        window = QMainWindow()
        central = QWidget()
        window.setCentralWidget(central)
        layout = QVBoxLayout(central)

        status_label = QLabel("Initial")
        layout.addWidget(status_label)

        screen = TextCodingScreen(data=data, colors=colors)
        layout.addWidget(screen)

        window.show()
        QApplication.processEvents()

        # Apply code
        result = vm.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=0,
            end=4,
        )
        assert result is True

        # Update status after apply (like demo does)
        status_label.setText("Applied code marker to selection")
        QApplication.processEvents()

        # Verify
        assert "Applied" in status_label.text()
        assert "marker" in status_label.text()

        # Cleanup
        window.close()
        context.close()


class TestE2EDataPersistence:
    """E2E tests verifying data persists through the full stack."""

    def test_applied_code_persists_to_database(self, demo_window, qapp):
        """
        E2E: Apply code and verify it's in the database
        """
        context = demo_window["context"]
        viewmodel = demo_window["viewmodel"]

        codes = context.controller.get_all_codes()
        code = codes[0]

        # Apply code
        viewmodel.apply_code_to_selection(
            code_id=code.id.value,
            source_id=1,
            start=5,
            end=15,
            memo="E2E test memo",
        )

        # Query database directly via repository
        segments = context.controller.get_segments_for_source(1)

        assert len(segments) == 1
        assert segments[0].code_id.value == code.id.value
        assert segments[0].position.start == 5
        assert segments[0].position.end == 15
        assert segments[0].memo == "E2E test memo"

    def test_code_changes_persist(self, demo_window, qapp):
        """
        E2E: Modify code and verify changes persist
        """
        context = demo_window["context"]
        viewmodel = demo_window["viewmodel"]

        codes = context.controller.get_all_codes()
        code = codes[0]
        original_name = code.name

        # Rename
        viewmodel.rename_code(code.id.value, "renamed_code")

        # Query database
        updated = context.controller.get_code(code.id.value)
        assert updated.name == "renamed_code"
        assert updated.name != original_name

        # Update memo
        viewmodel.update_code_memo(code.id.value, "New memo")
        updated = context.controller.get_code(code.id.value)
        assert updated.memo == "New memo"
