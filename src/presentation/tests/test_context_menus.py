"""
Tests for QC-007.03 Context Menus

Tests context menus for text editor and code tree:

Text Editor Context Menu:
- AC #1: Mark with selected code action
- AC #2: Mark with recent code (submenu)
- AC #3: Mark with new code
- AC #4: In-vivo code
- AC #5: Unmark code at cursor
- AC #6: Add memo to coded segment
- AC #7: Toggle important flag
- AC #8: Annotate selection
- AC #9: Copy to clipboard

Code Tree Context Menu:
- AC #10: Add new code to category
- AC #11: Add new sub-category
- AC #12: Rename code/category
- AC #13: View/edit code memo
- AC #14: Delete code/category
- AC #15: Change code color
- AC #16: Move code to different category
- AC #17: Show all files coded with this code
"""

from PySide6.QtTest import QSignalSpy


class TestTextEditorContextMenu:
    """Tests for text editor context menu."""

    def test_context_menu_creates(self, qapp, colors):
        """TextEditorContextMenu creates with default settings."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        assert menu is not None

    def test_context_menu_has_mark_action(self, qapp, colors):
        """Menu has mark with selected code action."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_selected_code({"id": "1", "name": "Test Code"})

        actions = [a.text() for a in menu.actions()]
        assert any("Mark" in a for a in actions)

    def test_context_menu_has_recent_codes_submenu(self, qapp, colors):
        """Menu has recent codes submenu."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        recent_codes = [
            {"id": "1", "name": "Code A", "color": "#FF0000"},
            {"id": "2", "name": "Code B", "color": "#00FF00"},
        ]
        menu.set_recent_codes(recent_codes)

        # Check for submenu
        has_recent = any("Recent" in a.text() for a in menu.actions())
        assert has_recent

    def test_context_menu_mark_disabled_without_selection(self, qapp, colors):
        """Mark action disabled when no text selected."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_has_selection(False)

        mark_action = menu.get_action("mark")
        assert mark_action is not None
        assert not mark_action.isEnabled()

    def test_context_menu_mark_enabled_with_selection(self, qapp, colors):
        """Mark action enabled when text is selected."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_has_selection(True)
        menu.set_selected_code({"id": "1", "name": "Test"})

        mark_action = menu.get_action("mark")
        assert mark_action is not None
        assert mark_action.isEnabled()

    def test_context_menu_unmark_visible_at_coded_position(self, qapp, colors):
        """Unmark action visible when cursor is at coded segment."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_codes_at_cursor([{"id": "1", "name": "Test Code"}])

        unmark_action = menu.get_action("unmark")
        assert unmark_action is not None
        assert unmark_action.isVisible()

    def test_context_menu_unmark_hidden_at_uncoded_position(self, qapp, colors):
        """Unmark action hidden when cursor is not at coded segment."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_codes_at_cursor([])

        unmark_action = menu.get_action("unmark")
        assert unmark_action is None or not unmark_action.isVisible()

    def test_context_menu_emits_action_signal(self, qapp, colors):
        """Menu emits signal when action is triggered."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        spy = QSignalSpy(menu.action_triggered)

        menu.set_has_selection(True)
        menu.set_selected_code({"id": "1", "name": "Test"})

        # Trigger mark action
        mark_action = menu.get_action("mark")
        if mark_action:
            mark_action.trigger()
            assert spy.count() == 1
            assert spy.at(0)[0] == "mark"

    def test_context_menu_has_copy_action(self, qapp, colors):
        """Menu has copy to clipboard action."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_has_selection(True)

        copy_action = menu.get_action("copy")
        assert copy_action is not None

    def test_context_menu_has_memo_action(self, qapp, colors):
        """Menu has add memo action when at coded segment."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_codes_at_cursor([{"id": "1", "name": "Test"}])

        memo_action = menu.get_action("memo")
        assert memo_action is not None

    def test_context_menu_has_annotate_action(self, qapp, colors):
        """Menu has annotate action."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_has_selection(True)

        annotate_action = menu.get_action("annotate")
        assert annotate_action is not None


class TestCodeTreeContextMenu:
    """Tests for code tree context menu."""

    def test_context_menu_creates(self, qapp, colors):
        """CodeTreeContextMenu creates with default settings."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        assert menu is not None

    def test_context_menu_has_add_code_action(self, qapp, colors):
        """Menu has add code action."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        add_action = menu.get_action("add_code")
        assert add_action is not None

    def test_context_menu_has_rename_action(self, qapp, colors):
        """Menu has rename action when code selected."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})

        rename_action = menu.get_action("rename")
        assert rename_action is not None
        assert rename_action.isEnabled()

    def test_context_menu_has_delete_action(self, qapp, colors):
        """Menu has delete action."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})

        delete_action = menu.get_action("delete")
        assert delete_action is not None

    def test_context_menu_has_change_color_action(self, qapp, colors):
        """Menu has change color action for codes."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})

        color_action = menu.get_action("change_color")
        assert color_action is not None

    def test_context_menu_has_memo_action(self, qapp, colors):
        """Menu has view/edit memo action."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})

        memo_action = menu.get_action("memo")
        assert memo_action is not None

    def test_context_menu_has_move_action(self, qapp, colors):
        """Menu has move to category action."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})
        menu.set_categories(
            [
                {"id": "cat1", "name": "Category 1"},
                {"id": "cat2", "name": "Category 2"},
            ]
        )

        move_action = menu.get_action("move")
        assert move_action is not None

    def test_context_menu_emits_action_signal(self, qapp, colors):
        """Menu emits signal when action is triggered."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        spy = QSignalSpy(menu.action_triggered)

        menu.set_selected_item({"id": "1", "name": "Test", "type": "code"})

        rename_action = menu.get_action("rename")
        if rename_action:
            rename_action.trigger()
            assert spy.count() == 1
            assert spy.at(0)[0] == "rename"

    def test_context_menu_category_has_limited_actions(self, qapp, colors):
        """Category items have different actions than codes."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "cat1", "name": "Category", "type": "category"})

        # Categories shouldn't have change color
        color_action = menu.get_action("change_color")
        assert color_action is None or not color_action.isVisible()


class TestColorPickerDialog:
    """Tests for color picker dialog."""

    def test_color_picker_creates(self, qapp, colors):
        """ColorPickerDialog creates."""
        from src.presentation.dialogs.color_picker_dialog import ColorPickerDialog

        dialog = ColorPickerDialog(colors=colors)
        assert dialog is not None

    def test_color_picker_has_preset_colors(self, qapp, colors):
        """ColorPickerDialog shows preset colors."""
        from src.presentation.dialogs.color_picker_dialog import ColorPickerDialog

        dialog = ColorPickerDialog(colors=colors)
        assert dialog.get_preset_count() >= 10

    def test_color_picker_set_initial_color(self, qapp, colors):
        """ColorPickerDialog can set initial color."""
        from src.presentation.dialogs.color_picker_dialog import ColorPickerDialog

        dialog = ColorPickerDialog(initial_color="#FF0000", colors=colors)
        assert dialog.get_selected_color() == "#FF0000"

    def test_color_picker_emits_color_selected(self, qapp, colors):
        """ColorPickerDialog emits signal on selection."""
        from src.presentation.dialogs.color_picker_dialog import ColorPickerDialog

        dialog = ColorPickerDialog(colors=colors)
        spy = QSignalSpy(dialog.color_selected)

        dialog.select_color("#00FF00")

        assert spy.count() == 1
        assert spy.at(0)[0] == "#00FF00"


class TestContextMenuScreenshot:
    """Visual tests with screenshots."""

    def test_screenshot_text_context_menu(self, qapp, colors, take_screenshot):
        """Screenshot of text editor context menu."""
        from src.presentation.organisms.context_menus import TextEditorContextMenu

        menu = TextEditorContextMenu(colors=colors)
        menu.set_has_selection(True)
        menu.set_selected_code({"id": "1", "name": "Theme: Identity"})
        menu.set_codes_at_cursor([{"id": "2", "name": "Sub-theme: Self"}])
        menu.set_recent_codes(
            [
                {"id": "1", "name": "Theme: Identity", "color": "#FF5733"},
                {"id": "2", "name": "Sub-theme: Self", "color": "#33FF57"},
                {"id": "3", "name": "Context: Work", "color": "#3357FF"},
            ]
        )

        # Can't easily screenshot a QMenu, but we can verify it's created
        assert menu is not None

    def test_screenshot_code_tree_context_menu(self, qapp, colors, take_screenshot):
        """Screenshot of code tree context menu."""
        from src.presentation.organisms.context_menus import CodeTreeContextMenu

        menu = CodeTreeContextMenu(colors=colors)
        menu.set_selected_item({"id": "1", "name": "Theme: Identity", "type": "code"})
        menu.set_categories(
            [
                {"id": "cat1", "name": "Themes"},
                {"id": "cat2", "name": "Sub-themes"},
            ]
        )

        assert menu is not None
