"""
Tests for data display components: DataTable, InfoCard, KeyValueList, EmptyState, etc.
"""

import pytest
from PyQt6.QtCore import Qt

from design_system.data_display import (
    DataTable, FileCell, EntityCell, InfoCard, CodeDetailCard,
    StatRow, KeyValueList, EmptyState
)


class TestDataTable:
    """Tests for DataTable component"""

    def test_table_creation(self, qtbot):
        """DataTable should be created with columns"""
        table = DataTable(columns=["Name", "Type", "Size"])
        qtbot.addWidget(table)

        assert table is not None
        assert len(table._columns) == 3

    def test_table_set_data(self, qtbot):
        """DataTable should display data"""
        table = DataTable(columns=["Name", "Value"])
        qtbot.addWidget(table)

        table.set_data([
            {"Name": "Item 1", "Value": "100"},
            {"Name": "Item 2", "Value": "200"},
        ])

        assert len(table._data) == 2

    def test_table_row_click_signal(self, qtbot):
        """DataTable should emit row_clicked signal"""
        table = DataTable(columns=["Name"])
        qtbot.addWidget(table)

        table.set_data([{"Name": "Test"}])

        # Signal should exist
        assert hasattr(table, 'row_clicked')

    def test_table_selectable(self, qtbot):
        """DataTable should support selection"""
        table = DataTable(columns=["Name"], selectable=True)
        qtbot.addWidget(table)

        assert table._selectable is True


class TestFileCell:
    """Tests for FileCell component"""

    def test_file_cell_creation(self, qtbot):
        """FileCell should display file info"""
        cell = FileCell(name="document.txt", file_type="text", size="12 KB")
        qtbot.addWidget(cell)

        assert cell is not None

    def test_file_cell_types(self, qtbot):
        """FileCell should support different file types"""
        types = ["text", "audio", "video", "image", "pdf"]

        for ft in types:
            cell = FileCell(name=f"file.{ft}", file_type=ft)
            qtbot.addWidget(cell)
            assert cell is not None


class TestEntityCell:
    """Tests for EntityCell component"""

    def test_entity_cell_creation(self, qtbot):
        """EntityCell should display entity info"""
        cell = EntityCell(name="John Doe", subtitle="Participant")
        qtbot.addWidget(cell)

        assert cell is not None

    def test_entity_cell_avatar(self, qtbot):
        """EntityCell should show avatar"""
        cell = EntityCell(name="Jane", avatar="J")
        qtbot.addWidget(cell)

        assert cell is not None


class TestInfoCard:
    """Tests for InfoCard component"""

    def test_info_card_creation(self, qtbot):
        """InfoCard should be created with title"""
        card = InfoCard(title="Statistics")
        qtbot.addWidget(card)

        assert card is not None
        assert card._title_label.text() == "Statistics"

    def test_info_card_with_icon(self, qtbot):
        """InfoCard should support qtawesome icon"""
        card = InfoCard(title="Info", icon="mdi6.information")
        qtbot.addWidget(card)

        assert card is not None
        assert hasattr(card, '_icon_widget')

    def test_info_card_set_text(self, qtbot):
        """InfoCard should set text content"""
        card = InfoCard(title="Details")
        qtbot.addWidget(card)

        card.set_text("This is the content")
        assert card._content_layout.count() == 1

    def test_info_card_set_content_widget(self, qtbot):
        """InfoCard should accept widget content"""
        from PyQt6.QtWidgets import QLabel
        card = InfoCard(title="Custom")
        qtbot.addWidget(card)

        label = QLabel("Custom widget")
        card.set_content(label)
        assert card._content_layout.count() == 1

    def test_info_card_collapsible(self, qtbot):
        """InfoCard should support collapse/expand"""
        card = InfoCard(title="Collapsible", collapsible=True)
        qtbot.addWidget(card)

        assert card._collapsible is True
        assert card.is_collapsed() is False

        card._toggle_collapse()
        assert card.is_collapsed() is True

    def test_info_card_starts_collapsed(self, qtbot):
        """InfoCard should start collapsed when specified"""
        card = InfoCard(title="Test", collapsible=True, collapsed=True)
        qtbot.addWidget(card)

        assert card.is_collapsed() is True

    def test_info_card_set_title(self, qtbot):
        """InfoCard should update title"""
        card = InfoCard(title="Original")
        qtbot.addWidget(card)

        card.set_title("Updated")
        assert card._title_label.text() == "Updated"


class TestCodeDetailCard:
    """Tests for CodeDetailCard component"""

    def test_code_detail_creation(self, qtbot):
        """CodeDetailCard should be created"""
        card = CodeDetailCard(
            color="#FFC107",
            name="test code",
            memo="A test code description"
        )
        qtbot.addWidget(card)

        assert card is not None
        assert card._name_label.text() == "test code"

    def test_code_detail_with_example(self, qtbot):
        """CodeDetailCard should show example text"""
        card = CodeDetailCard(
            color="#4CAF50",
            name="example code",
            memo="Description",
            example="This is example text"
        )
        qtbot.addWidget(card)

        assert card is not None

    def test_code_detail_set_code(self, qtbot):
        """CodeDetailCard should update code details"""
        card = CodeDetailCard(color="#FF0000", name="old")
        qtbot.addWidget(card)

        card.set_code(color="#00FF00", name="new", memo="new memo")
        assert card._name_label.text() == "new"
        assert card._code_color == "#00FF00"

    def test_code_detail_signals(self, qtbot):
        """CodeDetailCard should have edit/delete signals"""
        card = CodeDetailCard(color="#009688", name="code")
        qtbot.addWidget(card)

        assert hasattr(card, 'edit_clicked')
        assert hasattr(card, 'delete_clicked')


class TestStatRow:
    """Tests for StatRow component"""

    def test_stat_row_creation(self, qtbot):
        """StatRow should display label and value"""
        row = StatRow(label="Files", value="24")
        qtbot.addWidget(row)

        assert row is not None


class TestKeyValueList:
    """Tests for KeyValueList component"""

    def test_kv_list_creation(self, qtbot):
        """KeyValueList should be created"""
        kvlist = KeyValueList()
        qtbot.addWidget(kvlist)

        assert kvlist is not None

    def test_kv_list_add_items(self, qtbot):
        """KeyValueList should add items"""
        kvlist = KeyValueList()
        qtbot.addWidget(kvlist)

        kvlist.add_item("Name", "Test Project")
        kvlist.add_item("Version", "1.0.0")

        # Should have items in layout
        assert kvlist._layout.count() == 2

    def test_kv_list_separator(self, qtbot):
        """KeyValueList should add separators"""
        kvlist = KeyValueList()
        qtbot.addWidget(kvlist)

        kvlist.add_item("A", "1")
        kvlist.add_separator()
        kvlist.add_item("B", "2")

        assert kvlist._layout.count() == 3


class TestEmptyState:
    """Tests for EmptyState component"""

    def test_empty_state_creation(self, qtbot):
        """EmptyState should be created"""
        empty = EmptyState(title="No files", message="Upload files to get started")
        qtbot.addWidget(empty)

        assert empty is not None

    def test_empty_state_with_icon(self, qtbot):
        """EmptyState should support icon"""
        empty = EmptyState(icon="📁", title="Empty", message="Nothing here")
        qtbot.addWidget(empty)

        assert empty is not None

    def test_empty_state_with_action(self, qtbot):
        """EmptyState should support action button"""
        clicked = []

        empty = EmptyState(
            title="No files",
            message="Upload to start",
            action_text="Upload",
            on_action=lambda: clicked.append(True)
        )
        qtbot.addWidget(empty)

        # Should have action button
        assert empty is not None
