"""
Tests for list components: FileList, CaseList, QueueList, etc.
"""

from PySide6.QtCore import Qt

from design_system.lists import (
    AttributeList,
    CaseList,
    CaseListItem,
    FileList,
    FileListItem,
    QueueList,
)


class TestFileList:
    """Tests for FileList component"""

    def test_file_list_creation(self, qtbot):
        """FileList should be created"""
        lst = FileList()
        qtbot.addWidget(lst)

        assert lst is not None

    def test_file_list_add_file(self, qtbot):
        """FileList should add files"""
        lst = FileList()
        qtbot.addWidget(lst)

        lst.add_file("1", "document.txt", "text", "12 KB")
        lst.add_file("2", "audio.mp3", "audio", "5 MB")

        assert len(lst._items) == 2

    def test_file_list_set_files(self, qtbot):
        """FileList should set files from list"""
        lst = FileList()
        qtbot.addWidget(lst)

        lst.set_files(
            [
                {"id": "1", "name": "file1.txt", "type": "text", "size": "1 KB"},
                {"id": "2", "name": "file2.txt", "type": "text", "size": "2 KB"},
            ]
        )

        assert len(lst._items) == 2

    def test_file_list_clear(self, qtbot):
        """FileList should clear items"""
        lst = FileList()
        qtbot.addWidget(lst)

        lst.add_file("1", "file.txt", "text")
        lst.clear()

        assert len(lst._items) == 0

    def test_file_list_click_signal(self, qtbot):
        """FileList should emit item_clicked signal"""
        lst = FileList()
        qtbot.addWidget(lst)

        lst.add_file("1", "test.txt", "text")

        with qtbot.waitSignal(lst.item_clicked, timeout=1000):
            item = lst._items[0]
            qtbot.mouseClick(item, Qt.MouseButton.LeftButton)


class TestFileListItem:
    """Tests for FileListItem component"""

    def test_item_creation(self, qtbot):
        """FileListItem should be created"""
        item = FileListItem(id="1", name="test.txt", file_type="text", size="5 KB")
        qtbot.addWidget(item)

        assert item is not None

    def test_item_with_status(self, qtbot):
        """FileListItem should show status badge"""
        item = FileListItem(
            id="1", name="test.txt", file_type="text", size="5 KB", status="coded"
        )
        qtbot.addWidget(item)

        assert item is not None

    def test_item_click_signal(self, qtbot):
        """FileListItem should emit clicked signal"""
        item = FileListItem(id="1", name="test.txt", file_type="text", size="5 KB")
        qtbot.addWidget(item)

        with qtbot.waitSignal(item.clicked, timeout=1000):
            qtbot.mouseClick(item, Qt.MouseButton.LeftButton)


class TestCaseList:
    """Tests for CaseList component"""

    def test_case_list_creation(self, qtbot):
        """CaseList should be created"""
        lst = CaseList()
        qtbot.addWidget(lst)

        assert lst is not None

    def test_case_list_add_case(self, qtbot):
        """CaseList should add cases"""
        lst = CaseList()
        qtbot.addWidget(lst)

        lst.add_case("1", "Participant 01", "3 files")
        lst.add_case("2", "Participant 02", "5 files")

        assert len(lst._items) == 2

    def test_case_list_with_color(self, qtbot):
        """CaseList should support avatar colors"""
        lst = CaseList()
        qtbot.addWidget(lst)

        lst.add_case("1", "Test", color="#FF5722")

        assert len(lst._items) == 1


class TestCaseListItem:
    """Tests for CaseListItem component"""

    def test_item_creation(self, qtbot):
        """CaseListItem should be created"""
        item = CaseListItem(id="1", name="John Doe", subtitle="Participant", avatar="J")
        qtbot.addWidget(item)

        assert item is not None

    def test_item_click_signal(self, qtbot):
        """CaseListItem should emit clicked signal"""
        item = CaseListItem(id="1", name="Test", subtitle="", avatar="T")
        qtbot.addWidget(item)

        with qtbot.waitSignal(item.clicked, timeout=1000):
            qtbot.mouseClick(item, Qt.MouseButton.LeftButton)


class TestQueueList:
    """Tests for QueueList component"""

    def test_queue_list_creation(self, qtbot):
        """QueueList should be created"""
        lst = QueueList()
        qtbot.addWidget(lst)

        assert lst is not None

    def test_queue_list_add_item(self, qtbot):
        """QueueList should add items"""
        lst = QueueList()
        qtbot.addWidget(lst)

        lst.add_item("1", "Create new code", "pending", "John")
        lst.add_item("2", "Review changes", "reviewing", "Jane")

        assert len(lst._items) == 2

    def test_queue_list_statuses(self, qtbot):
        """QueueList should support different statuses"""
        lst = QueueList()
        qtbot.addWidget(lst)

        statuses = ["pending", "reviewing", "approved", "rejected"]
        for i, status in enumerate(statuses):
            lst.add_item(str(i), f"Task {i}", status)

        assert len(lst._items) == 4


class TestAttributeList:
    """Tests for AttributeList component"""

    def test_attribute_list_creation(self, qtbot):
        """AttributeList should be created"""
        lst = AttributeList()
        qtbot.addWidget(lst)

        assert lst is not None

    def test_attribute_list_add_attribute(self, qtbot):
        """AttributeList should add attributes"""
        lst = AttributeList()
        qtbot.addWidget(lst)

        lst.add_attribute("1", "Age", "numeric")
        lst.add_attribute("2", "Gender", "text")

        assert len(lst._items) == 2

    def test_attribute_types(self, qtbot):
        """AttributeList should support attribute types"""
        lst = AttributeList()
        qtbot.addWidget(lst)

        lst.add_attribute("1", "Count", "numeric")
        lst.add_attribute("2", "Name", "text")

        assert len(lst._items) == 2
