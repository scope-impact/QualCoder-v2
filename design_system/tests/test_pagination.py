"""
Tests for pagination components: Pagination, SimplePagination, etc.
"""

from PySide6.QtCore import Qt

from design_system.pagination import (
    PageButton,
    Pagination,
    PaginationInfo,
    SimplePagination,
)


class TestPagination:
    """Tests for Pagination component"""

    def test_pagination_creation(self, qtbot):
        """Pagination should be created"""
        pagination = Pagination(total_pages=10, current_page=1)
        qtbot.addWidget(pagination)

        assert pagination is not None
        assert pagination.total_pages() == 10
        assert pagination.current_page() == 1

    def test_pagination_set_page(self, qtbot):
        """Pagination should update current page"""
        pagination = Pagination(total_pages=10, current_page=1)
        qtbot.addWidget(pagination)

        pagination.set_page(5)
        assert pagination.current_page() == 5

    def test_pagination_set_total(self, qtbot):
        """Pagination should update total pages"""
        pagination = Pagination(total_pages=10, current_page=1)
        qtbot.addWidget(pagination)

        pagination.set_total_pages(20)
        assert pagination.total_pages() == 20

    def test_pagination_bounds(self, qtbot):
        """Pagination should respect bounds"""
        pagination = Pagination(total_pages=10, current_page=1)
        qtbot.addWidget(pagination)

        # Can't go below 1
        pagination.set_page(0)
        assert pagination.current_page() >= 1

        # Can't go above total
        pagination.set_page(100)
        assert pagination.current_page() <= 10

    def test_pagination_signal(self, qtbot):
        """Pagination should emit page_changed signal"""
        pagination = Pagination(total_pages=10, current_page=1)
        qtbot.addWidget(pagination)

        # Signal should exist
        assert hasattr(pagination, "page_changed")


class TestPageButton:
    """Tests for PageButton component"""

    def test_page_button_creation(self, qtbot):
        """PageButton should be created"""
        btn = PageButton(page=5)
        qtbot.addWidget(btn)

        assert btn.text() == "5"

    def test_page_button_active(self, qtbot):
        """PageButton should support active state"""
        btn = PageButton(page=3, active=False)
        qtbot.addWidget(btn)

        btn.setActive(True)
        assert btn._active is True


class TestPaginationInfo:
    """Tests for PaginationInfo component"""

    def test_info_creation(self, qtbot):
        """PaginationInfo should be created"""
        info = PaginationInfo(current_start=1, current_end=10, total=100)
        qtbot.addWidget(info)

        assert info is not None

    def test_info_update(self, qtbot):
        """PaginationInfo should update text"""
        info = PaginationInfo(current_start=1, current_end=10, total=100)
        qtbot.addWidget(info)

        info.update_info(11, 20, 100)

        # Label should contain updated numbers
        assert "11" in info._label.text()
        assert "20" in info._label.text()


class TestSimplePagination:
    """Tests for SimplePagination component"""

    def test_simple_creation(self, qtbot):
        """SimplePagination should be created"""
        pagination = SimplePagination(current=1, total=10)
        qtbot.addWidget(pagination)

        assert pagination is not None
        assert pagination._current == 1
        assert pagination._total == 10

    def test_simple_navigation(self, qtbot):
        """SimplePagination should navigate pages"""
        pagination = SimplePagination(current=5, total=10)
        qtbot.addWidget(pagination)

        # Go next
        qtbot.mouseClick(pagination._next_btn, Qt.MouseButton.LeftButton)
        assert pagination._current == 6

        # Go prev
        qtbot.mouseClick(pagination._prev_btn, Qt.MouseButton.LeftButton)
        assert pagination._current == 5

    def test_simple_bounds(self, qtbot):
        """SimplePagination should respect bounds"""
        pagination = SimplePagination(current=1, total=3)
        qtbot.addWidget(pagination)

        # At first page, prev should be disabled
        assert not pagination._prev_btn.isEnabled()

        # Go to last page
        pagination.set_page(3)
        assert not pagination._next_btn.isEnabled()

    def test_simple_signal(self, qtbot):
        """SimplePagination should emit page_changed signal"""
        pagination = SimplePagination(current=1, total=10)
        qtbot.addWidget(pagination)

        with qtbot.waitSignal(pagination.page_changed, timeout=1000):
            qtbot.mouseClick(pagination._next_btn, Qt.MouseButton.LeftButton)
