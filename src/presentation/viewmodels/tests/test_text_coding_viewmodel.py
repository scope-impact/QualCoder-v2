"""
Tests for TextCodingViewModel.

Tests the full data flow from ViewModel through Controller to ensure
presentation layer receives correct data for UI rendering.
"""

from PySide6.QtTest import QSignalSpy


class TestViewModelCodeManagement:
    """Tests for code management operations."""

    def test_create_code_returns_true(self, qapp, viewmodel):
        """Test that create_code returns True on success."""
        result = viewmodel.create_code("test_code", "#ff0000")
        assert result is True

    def test_create_code_emits_codes_changed(self, qapp, viewmodel):
        """Test that creating a code emits codes_changed signal."""
        spy = QSignalSpy(viewmodel.codes_changed)

        viewmodel.create_code("test_code", "#ff0000")

        assert spy.count() == 1

    def test_create_duplicate_code_returns_false(self, qapp, viewmodel):
        """Test that creating a duplicate code returns False."""
        viewmodel.create_code("test_code", "#ff0000")
        result = viewmodel.create_code("test_code", "#00ff00")

        assert result is False

    def test_create_duplicate_emits_error(self, qapp, viewmodel):
        """Test that creating a duplicate code emits error signal."""
        spy = QSignalSpy(viewmodel.error_occurred)

        viewmodel.create_code("test_code", "#ff0000")
        viewmodel.create_code("test_code", "#00ff00")

        assert spy.count() == 1

    def test_rename_code_success(self, qapp, viewmodel, coding_context):
        """Test renaming a code."""
        viewmodel.create_code("original_name", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        result = viewmodel.rename_code(code_id, "new_name")

        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.name == "new_name"

    def test_delete_code_success(self, qapp, viewmodel, coding_context):
        """Test deleting a code."""
        viewmodel.create_code("to_delete", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        result = viewmodel.delete_code(code_id)

        assert result is True
        assert coding_context.controller.get_code(code_id) is None

    def test_update_code_memo(self, qapp, viewmodel, coding_context):
        """Test updating a code's memo."""
        viewmodel.create_code("memo_test", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        result = viewmodel.update_code_memo(code_id, "This is a test memo")

        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.memo == "This is a test memo"

    def test_update_code_memo_to_none(self, qapp, viewmodel, coding_context):
        """Test clearing a code's memo."""
        viewmodel.create_code("memo_test", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        viewmodel.update_code_memo(code_id, "Initial memo")
        result = viewmodel.update_code_memo(code_id, None)

        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.memo is None

    def test_move_code_to_category(self, qapp, viewmodel, coding_context):
        """Test moving a code to a category."""
        viewmodel.create_category("Test Category")
        viewmodel.create_code("movable_code", "#ff0000")

        codes = coding_context.controller.get_all_codes()
        categories = coding_context.controller.get_all_categories()
        code_id = codes[0].id.value
        category_id = categories[0].id.value

        result = viewmodel.move_code_to_category(code_id, category_id)

        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.category_id is not None
        assert updated.category_id.value == category_id

    def test_move_code_to_uncategorized(self, qapp, viewmodel, coding_context):
        """Test moving a code back to uncategorized."""
        viewmodel.create_category("Test Category")
        viewmodel.create_code("movable_code", "#ff0000")

        codes = coding_context.controller.get_all_codes()
        categories = coding_context.controller.get_all_categories()
        code_id = codes[0].id.value
        category_id = categories[0].id.value

        # Move to category first
        viewmodel.move_code_to_category(code_id, category_id)

        # Move back to uncategorized
        result = viewmodel.move_code_to_category(code_id, None)

        assert result is True
        updated = coding_context.controller.get_code(code_id)
        assert updated.category_id is None


class TestViewModelCategoryManagement:
    """Tests for category management operations."""

    def test_create_category_returns_true(self, qapp, viewmodel):
        """Test that create_category returns True on success."""
        result = viewmodel.create_category("Test Category")
        assert result is True

    def test_create_nested_category(self, qapp, viewmodel, coding_context):
        """Test creating a nested category."""
        viewmodel.create_category("Parent")
        categories = coding_context.controller.get_all_categories()
        parent_id = categories[0].id.value

        result = viewmodel.create_category("Child", parent_id)

        assert result is True
        all_cats = coding_context.controller.get_all_categories()
        child = next(c for c in all_cats if c.name == "Child")
        assert child.parent_id is not None
        assert child.parent_id.value == parent_id


class TestViewModelSegmentOperations:
    """Tests for segment (coding) operations."""

    def test_apply_code_to_selection(self, qapp, viewmodel, coding_context):
        """Test applying a code to a text selection."""
        viewmodel.create_code("marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        result = viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=0,
            end=10,
            memo="Test segment",
        )

        assert result is True
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].code_id.value == code_id
        assert segments[0].position.start == 0
        assert segments[0].position.end == 10

    def test_remove_segment(self, qapp, viewmodel, coding_context):
        """Test removing a coded segment."""
        viewmodel.create_code("marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        viewmodel.apply_code_to_selection(code_id, 1, 0, 10)
        segments = coding_context.controller.get_segments_for_source(1)
        segment_id = segments[0].id.value

        result = viewmodel.remove_segment(segment_id)

        assert result is True
        remaining = coding_context.controller.get_segments_for_source(1)
        assert len(remaining) == 0


class TestViewModelLoadCodes:
    """Tests for loading codes and the data format returned."""

    def test_load_codes_returns_categories(self, qapp, viewmodel):
        """Test that load_codes returns a list of CodeCategoryDTO."""
        viewmodel.create_code("test_code", "#ff0000")

        categories = viewmodel.load_codes()

        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_load_codes_includes_code_ids(self, qapp, viewmodel, coding_context):
        """Test that loaded codes include numeric IDs.

        This is critical for the UI to correctly identify codes when clicked.
        """
        viewmodel.create_code("test_code", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        expected_id = str(codes[0].id.value)

        categories = viewmodel.load_codes()

        # Find the code in the returned data
        found_code = None
        for cat in categories:
            for code in cat.codes:
                if code.name == "test_code":
                    found_code = code
                    break

        assert found_code is not None
        assert found_code.id == expected_id
        # ID should be numeric (as string), not the name
        assert found_code.id != "test_code"

    def test_load_codes_groups_by_category(self, qapp, viewmodel, coding_context):
        """Test that codes are grouped by their category."""
        viewmodel.create_category("Emotions")
        categories = coding_context.controller.get_all_categories()
        cat_id = categories[0].id.value

        viewmodel.create_code("happy", "#00ff00", category_id=cat_id)
        viewmodel.create_code("sad", "#0000ff", category_id=cat_id)
        viewmodel.create_code("uncategorized_code", "#ff0000")

        loaded = viewmodel.load_codes()

        # Should have Emotions category and Uncategorized
        cat_names = [c.name for c in loaded]
        assert "Emotions" in cat_names
        assert "Uncategorized" in cat_names

        # Emotions should have happy and sad
        emotions_cat = next(c for c in loaded if c.name == "Emotions")
        code_names = [c.name for c in emotions_cat.codes]
        assert "happy" in code_names
        assert "sad" in code_names

    def test_load_codes_includes_segment_count(self, qapp, viewmodel, coding_context):
        """Test that code count reflects number of segments."""
        viewmodel.create_code("marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        # Apply code twice
        viewmodel.apply_code_to_selection(code_id, 1, 0, 10)
        viewmodel.apply_code_to_selection(code_id, 1, 20, 30)

        categories = viewmodel.load_codes()
        found_code = None
        for cat in categories:
            for code in cat.codes:
                if code.name == "marker":
                    found_code = code
                    break

        assert found_code is not None
        assert found_code.count == 2


class TestViewModelUIIntegration:
    """Tests for ViewModel integration with UI components."""

    def test_codes_panel_receives_correct_ids(
        self, qapp, viewmodel, coding_context, colors
    ):
        """Test that CodesPanel receives and stores correct code IDs.

        This is the integration test that would have caught the bug where
        code names were used as IDs instead of numeric IDs.
        """
        from src.presentation.organisms import CodesPanel

        # Create codes
        viewmodel.create_code("positive", "#00ff00")
        viewmodel.create_code("negative", "#ff0000")

        # Get the actual code IDs from the backend
        codes = coding_context.controller.get_all_codes()
        code_ids = {c.name: str(c.id.value) for c in codes}

        # Load codes like the viewmodel does
        categories = viewmodel.load_codes()

        # Convert to dict format like demo_connected does
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

        # Create panel and set codes
        panel = CodesPanel(colors=colors)
        panel.set_codes(cat_dicts)

        # Verify the tree items have numeric IDs, not names
        items = panel._code_tree._items
        for cat_item in items:
            for code_item in cat_item.children:
                # The ID should be numeric, not the same as the name
                if code_item.name in code_ids:
                    assert code_item.id == code_ids[code_item.name]
                    assert code_item.id != code_item.name

    def test_full_apply_code_flow(self, qapp, viewmodel, coding_context, colors):
        """Test the complete flow of selecting and applying a code.

        This simulates what happens when a user:
        1. Creates a code
        2. Selects text
        3. Clicks a code in the UI
        4. Applies the code
        """
        from PySide6.QtTest import QSignalSpy

        from src.presentation.organisms import CodesPanel

        # 1. Create a code
        viewmodel.create_code("important", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        expected_code_id = codes[0].id.value

        # 2. Load and set codes in panel (simulating UI setup)
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

        # 3. Simulate clicking the code (get the ID from tree item)
        code_item = panel._code_tree._items[0].children[0]
        clicked_id = code_item.id

        spy = QSignalSpy(panel.code_selected)
        panel._on_code_click(clicked_id)

        # 4. Get the emitted ID and apply the code
        emitted_data = spy.at(0)[0]
        selected_code_id = int(emitted_data["id"])

        # 5. Apply code using the selected ID
        result = viewmodel.apply_code_to_selection(
            code_id=selected_code_id,
            source_id=1,
            start=0,
            end=10,
        )

        # Verify the code was applied with the correct ID
        assert result is True
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].code_id.value == expected_code_id
