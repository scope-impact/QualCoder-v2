"""
Pagination components
Page navigation and pagination controls
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class Pagination(QFrame):
    """
    Pagination control with page numbers and navigation.

    Usage:
        pagination = Pagination(total_pages=10, current_page=1)
        pagination.page_changed.connect(self.load_page)
    """

    page_changed = pyqtSignal(int)

    def __init__(
        self,
        total_pages: int = 1,
        current_page: int = 1,
        show_first_last: bool = True,
        max_visible: int = 5,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._total_pages = total_pages
        self._current_page = current_page
        self._show_first_last = show_first_last
        self._max_visible = max_visible

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.xs)

        self._build()

    def _build(self):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # First button
        if self._show_first_last:
            first_btn = self._create_nav_btn("«", self._current_page > 1)
            first_btn.clicked.connect(lambda: self._go_to_page(1))
            self._layout.addWidget(first_btn)

        # Previous button
        prev_btn = self._create_nav_btn("‹", self._current_page > 1)
        prev_btn.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        self._layout.addWidget(prev_btn)

        # Page numbers
        pages = self._calculate_visible_pages()
        for page in pages:
            if page == "...":
                ellipsis = QLabel("...")
                ellipsis.setStyleSheet(f"""
                    color: {self._colors.text_secondary};
                    padding: 0 {SPACING.xs}px;
                """)
                self._layout.addWidget(ellipsis)
            else:
                btn = PageButton(
                    page=page,
                    active=(page == self._current_page),
                    colors=self._colors
                )
                btn.clicked.connect(lambda checked, p=page: self._go_to_page(p))
                self._layout.addWidget(btn)

        # Next button
        next_btn = self._create_nav_btn("›", self._current_page < self._total_pages)
        next_btn.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        self._layout.addWidget(next_btn)

        # Last button
        if self._show_first_last:
            last_btn = self._create_nav_btn("»", self._current_page < self._total_pages)
            last_btn.clicked.connect(lambda: self._go_to_page(self._total_pages))
            self._layout.addWidget(last_btn)

    def _create_nav_btn(self, text: str, enabled: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setEnabled(enabled)
        btn.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_primary if enabled else self._colors.text_disabled};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                font-size: 14px;
            }}
            QPushButton:hover:enabled {{
                background-color: {self._colors.surface_light};
                border-color: {self._colors.primary};
            }}
        """)
        return btn

    def _calculate_visible_pages(self):
        """Calculate which page numbers to show"""
        if self._total_pages <= self._max_visible:
            return list(range(1, self._total_pages + 1))

        pages = []
        half = self._max_visible // 2

        # Always show first page
        pages.append(1)

        # Calculate middle range
        start = max(2, self._current_page - half + 1)
        end = min(self._total_pages - 1, self._current_page + half - 1)

        # Adjust if at edges
        if self._current_page <= half:
            end = self._max_visible - 1
        elif self._current_page > self._total_pages - half:
            start = self._total_pages - self._max_visible + 2

        # Add ellipsis and middle pages
        if start > 2:
            pages.append("...")
        for i in range(start, end + 1):
            pages.append(i)
        if end < self._total_pages - 1:
            pages.append("...")

        # Always show last page
        pages.append(self._total_pages)

        return pages

    def _go_to_page(self, page: int):
        if 1 <= page <= self._total_pages and page != self._current_page:
            self._current_page = page
            self._build()
            self.page_changed.emit(page)

    def set_page(self, page: int):
        if 1 <= page <= self._total_pages:
            self._current_page = page
            self._build()

    def set_total_pages(self, total: int):
        self._total_pages = max(1, total)
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        self._build()

    def current_page(self) -> int:
        return self._current_page

    def total_pages(self) -> int:
        return self._total_pages


class PageButton(QPushButton):
    """
    Individual page number button.

    Usage:
        btn = PageButton(page=5, active=False)
        btn.clicked.connect(self.go_to_page)
    """

    def __init__(
        self,
        page: int,
        active: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(str(page), parent)
        self._colors = colors or get_theme("dark")
        self._page = page
        self._active = active

        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_primary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.sm}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    border-color: {self._colors.primary};
                }}
            """)

    def setActive(self, active: bool):
        self._active = active
        self._apply_style()


class PaginationInfo(QFrame):
    """
    Pagination info display (e.g., "Showing 1-10 of 100").

    Usage:
        info = PaginationInfo(
            current_start=1,
            current_end=10,
            total=100
        )
    """

    def __init__(
        self,
        current_start: int = 1,
        current_end: int = 10,
        total: int = 100,
        item_name: str = "items",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(self._label)

        self.update_info(current_start, current_end, total, item_name)

    def update_info(
        self,
        current_start: int,
        current_end: int,
        total: int,
        item_name: str = None
    ):
        if item_name:
            self._item_name = item_name
        text = f"Showing {current_start}-{current_end} of {total} {self._item_name}"
        self._label.setText(text)


class SimplePagination(QFrame):
    """
    Simple previous/next pagination without page numbers.

    Usage:
        pagination = SimplePagination(current=5, total=20)
        pagination.page_changed.connect(self.load_page)
    """

    page_changed = pyqtSignal(int)

    def __init__(
        self,
        current: int = 1,
        total: int = 1,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._current = current
        self._total = total

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.md)

        # Previous
        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._go_prev)
        layout.addWidget(self._prev_btn)

        # Info
        self._info = QLabel()
        self._info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(self._info, 1)

        # Next
        self._next_btn = QPushButton("Next →")
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._go_next)
        layout.addWidget(self._next_btn)

        self._update()

    def _update(self):
        self._prev_btn.setEnabled(self._current > 1)
        self._next_btn.setEnabled(self._current < self._total)

        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover:enabled {{
                background-color: {self._colors.surface_light};
                border-color: {self._colors.primary};
            }}
            QPushButton:disabled {{
                color: {self._colors.text_disabled};
                border-color: {self._colors.border};
            }}
        """
        self._prev_btn.setStyleSheet(btn_style)
        self._next_btn.setStyleSheet(btn_style)

        self._info.setText(f"Page {self._current} of {self._total}")

    def _go_prev(self):
        if self._current > 1:
            self._current -= 1
            self._update()
            self.page_changed.emit(self._current)

    def _go_next(self):
        if self._current < self._total:
            self._current += 1
            self._update()
            self.page_changed.emit(self._current)

    def set_page(self, page: int):
        self._current = max(1, min(page, self._total))
        self._update()

    def set_total(self, total: int):
        self._total = max(1, total)
        if self._current > self._total:
            self._current = self._total
        self._update()
