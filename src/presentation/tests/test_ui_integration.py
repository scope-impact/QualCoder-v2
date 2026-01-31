"""
UI Integration Tests

Tests the complete flow from UI components through ViewModel to Controller,
verifying that user interactions result in correct data persistence and UI updates.

These tests simulate real user workflows and would catch bugs like:
- ID/name confusion in data passing
- Signal propagation failures
- Data transformation errors between layers
"""

from PySide6.QtTest import QSignalSpy

# Note: qapp, colors, coding_context, viewmodel fixtures come from conftest.py


class TestCodeSelectionFlow:
    """Test the complete code selection flow from UI click to data retrieval."""

    def test_click_code_emits_numeric_id(self, qapp, viewmodel, coding_context, colors):
        """
        Scenario: User clicks on a code in the sidebar
        Expected: The emitted signal contains the numeric ID, not the code name
        """
        from src.presentation.organisms import CodesPanel

        # Setup: Create a code
        viewmodel.create_code("important", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        expected_id = str(codes[0].id.value)

        # Setup: Load codes into panel
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

        panel = CodesPanel(colors=colors)
        panel.set_codes(cat_dicts)

        # Action: Simulate clicking the code
        spy = QSignalSpy(panel.code_selected)
        code_item = panel._code_tree._items[0].children[0]
        panel._on_code_click(code_item.id)

        # Assert: Signal contains numeric ID
        assert spy.count() == 1
        emitted_id = spy.at(0)[0]["id"]
        assert emitted_id == expected_id
        assert emitted_id != "important"  # Should NOT be the name

    def test_selected_code_can_be_applied(
        self, qapp, viewmodel, coding_context, colors
    ):
        """
        Scenario: User selects a code, then applies it to text
        Expected: The segment is created with the correct code ID
        """
        from src.presentation.organisms import CodesPanel

        # Setup: Create code and panel
        viewmodel.create_code("marker", "#00ff00")
        codes = coding_context.controller.get_all_codes()
        expected_code_id = codes[0].id.value

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

        panel = CodesPanel(colors=colors)
        panel.set_codes(cat_dicts)

        # Action 1: Click to select code
        spy = QSignalSpy(panel.code_selected)
        code_item = panel._code_tree._items[0].children[0]
        panel._on_code_click(code_item.id)

        # Action 2: Get the selected ID and apply
        selected_id = int(spy.at(0)[0]["id"])
        result = viewmodel.apply_code_to_selection(
            code_id=selected_id,
            source_id=1,
            start=0,
            end=20,
        )

        # Assert: Segment created with correct code
        assert result is True
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].code_id.value == expected_code_id


class TestApplyCodeFlow:
    """Test the complete apply code workflow."""

    def test_apply_code_creates_segment(self, qapp, viewmodel, coding_context):
        """
        Scenario: User applies a code to selected text
        Expected: A segment is created with correct position and code
        """
        # Setup
        viewmodel.create_code("highlight", "#ffff00")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        # Action
        result = viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=10,
            end=25,
            memo="Test annotation",
        )

        # Assert
        assert result is True
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].position.start == 10
        assert segments[0].position.end == 25
        assert segments[0].memo == "Test annotation"

    def test_apply_code_emits_segments_changed(self, qapp, viewmodel, coding_context):
        """
        Scenario: User applies a code
        Expected: segments_changed signal is emitted for reactive UI update
        """
        viewmodel.create_code("marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        # Set current source so signal is emitted
        viewmodel.set_current_source(1)

        spy = QSignalSpy(viewmodel.segments_changed)

        viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=0,
            end=10,
        )

        assert spy.count() == 1

    def test_apply_nonexistent_code_fails(self, qapp, viewmodel):
        """
        Scenario: User tries to apply a code that doesn't exist
        Expected: Operation fails and error signal is emitted
        """
        spy = QSignalSpy(viewmodel.error_occurred)

        result = viewmodel.apply_code_to_selection(
            code_id=99999,  # Non-existent
            source_id=1,
            start=0,
            end=10,
        )

        assert result is False
        assert spy.count() == 1


class TestCodeManagementFlow:
    """Test code CRUD operations through the UI layer."""

    def test_create_code_updates_panel(self, qapp, viewmodel, colors):
        """
        Scenario: User creates a new code
        Expected: codes_changed signal emitted, panel can display new code
        """
        from src.presentation.organisms import CodesPanel

        spy = QSignalSpy(viewmodel.codes_changed)

        # Action: Create code
        viewmodel.create_code("new_code", "#ff0000")

        # Assert: Signal emitted
        assert spy.count() == 1

        # Assert: Panel can display the new code
        categories = spy.at(0)[0]
        panel = CodesPanel(colors=colors)
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
        panel.set_codes(cat_dicts)

        # Find the code in the tree
        found = False
        for cat_item in panel._code_tree._items:
            for code_item in cat_item.children:
                if code_item.name == "new_code":
                    found = True
                    break
        assert found

    def test_rename_code_updates_display(self, qapp, viewmodel, coding_context):
        """
        Scenario: User renames a code
        Expected: codes_changed signal emitted with updated name
        """
        viewmodel.create_code("old_name", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        spy = QSignalSpy(viewmodel.codes_changed)

        # Action
        result = viewmodel.rename_code(code_id, "new_name")

        # Assert
        assert result is True
        assert spy.count() == 1

        # Verify the name changed
        updated = coding_context.controller.get_code(code_id)
        assert updated.name == "new_name"

    def test_delete_code_removes_from_panel(self, qapp, viewmodel, coding_context):
        """
        Scenario: User deletes a code
        Expected: codes_changed signal emitted, code no longer in list
        """
        viewmodel.create_code("to_delete", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        spy = QSignalSpy(viewmodel.codes_changed)

        # Action
        result = viewmodel.delete_code(code_id)

        # Assert
        assert result is True
        assert spy.count() == 1

        # Verify code is gone
        assert coding_context.controller.get_code(code_id) is None

    def test_update_memo_preserves_code(self, qapp, viewmodel, coding_context):
        """
        Scenario: User updates a code's memo
        Expected: Memo updated, code otherwise unchanged
        """
        viewmodel.create_code("memo_test", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value
        original_color = codes[0].color.to_hex()

        # Action
        result = viewmodel.update_code_memo(code_id, "New memo content")

        # Assert
        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.memo == "New memo content"
        assert updated.name == "memo_test"
        assert updated.color.to_hex() == original_color

    def test_move_code_to_category(self, qapp, viewmodel, coding_context):
        """
        Scenario: User drags a code to a different category
        Expected: Code's category updated, appears in new category in UI
        """
        viewmodel.create_category("Target Category")
        viewmodel.create_code("movable", "#ff0000")

        codes = coding_context.controller.get_all_codes()
        categories = coding_context.controller.get_all_categories()
        code_id = codes[0].id.value
        cat_id = categories[0].id.value

        # Action
        result = viewmodel.move_code_to_category(code_id, cat_id)

        # Assert
        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.category_id.value == cat_id

        # Verify it appears in the right category when loaded
        loaded = viewmodel.load_codes()
        target_cat = next((c for c in loaded if c.name == "Target Category"), None)
        assert target_cat is not None
        code_names = [c.name for c in target_cat.codes]
        assert "movable" in code_names


class TestScreenInitialization:
    """Test that screens initialize correctly with data."""

    def test_screen_with_dto_has_correct_code_ids(self, qapp, colors):
        """
        Scenario: Screen is created with TextCodingDataDTO
        Expected: Code IDs are preserved through DTO-to-dict conversion
        """
        from src.presentation.dto import (
            CodeCategoryDTO,
            CodeDTO,
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.screens import TextCodingScreen

        data = TextCodingDataDTO(
            files=[],
            categories=[
                CodeCategoryDTO(
                    id="cat1",
                    name="Emotions",
                    codes=[
                        CodeDTO(id="111", name="happy", color="#00ff00", count=5),
                        CodeDTO(id="222", name="sad", color="#0000ff", count=3),
                    ],
                )
            ],
            document=DocumentDTO(id="1", title="Test", badge="", content="Content"),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["user"],
            selected_coder="user",
        )

        screen = TextCodingScreen(data=data, colors=colors)

        # Verify IDs are preserved
        items = screen.page.codes_panel._code_tree._items
        code_items = items[0].children

        assert code_items[0].id == "111"
        assert code_items[0].name == "happy"
        assert code_items[1].id == "222"
        assert code_items[1].name == "sad"

    def test_screen_code_click_emits_correct_id(self, qapp, colors):
        """
        Scenario: User clicks a code in a freshly initialized screen
        Expected: Signal contains the numeric ID from the DTO
        """
        from src.presentation.dto import (
            CodeCategoryDTO,
            CodeDTO,
            DocumentDTO,
            NavigationDTO,
            TextCodingDataDTO,
        )
        from src.presentation.screens import TextCodingScreen

        data = TextCodingDataDTO(
            files=[],
            categories=[
                CodeCategoryDTO(
                    id="cat1",
                    name="Test",
                    codes=[
                        CodeDTO(id="12345", name="test_code", color="#ff0000", count=0),
                    ],
                )
            ],
            document=DocumentDTO(id="1", title="Test", badge="", content="Content"),
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["user"],
            selected_coder="user",
        )

        screen = TextCodingScreen(data=data, colors=colors)
        spy = QSignalSpy(screen.code_selected)

        # Click the code
        screen.page.codes_panel._on_code_click("12345")

        # Verify
        assert spy.count() == 1
        assert spy.at(0)[0]["id"] == "12345"


class TestErrorHandling:
    """Test error handling in the UI layer."""

    def test_duplicate_code_shows_error(self, qapp, viewmodel):
        """
        Scenario: User tries to create a code with duplicate name
        Expected: error_occurred signal emitted with message
        """
        viewmodel.create_code("existing", "#ff0000")

        spy = QSignalSpy(viewmodel.error_occurred)
        result = viewmodel.create_code("existing", "#00ff00")

        assert result is False
        assert spy.count() == 1
        assert "existing" in spy.at(0)[0].lower() or "duplicate" in spy.at(0)[0].lower()

    def test_invalid_color_shows_error(self, qapp, viewmodel):
        """
        Scenario: User enters invalid hex color
        Expected: error_occurred signal emitted
        """
        spy = QSignalSpy(viewmodel.error_occurred)
        result = viewmodel.create_code("test", "not-a-color")

        assert result is False
        assert spy.count() == 1

    def test_delete_nonexistent_code_shows_error(self, qapp, viewmodel):
        """
        Scenario: User tries to delete a code that doesn't exist
        Expected: error_occurred signal emitted
        """
        spy = QSignalSpy(viewmodel.error_occurred)
        result = viewmodel.delete_code(99999)

        assert result is False
        assert spy.count() == 1
