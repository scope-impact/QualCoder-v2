"""
Calendar components
Mini calendars, date pickers, and date navigation
"""

from typing import List, Optional
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class CalendarMini(QFrame):
    """
    Mini calendar widget for date selection.

    Usage:
        calendar = CalendarMini()
        calendar.date_selected.connect(self.on_date_select)
    """

    date_selected = pyqtSignal(object)  # date object

    def __init__(
        self,
        selected_date: date = None,
        highlight_dates: List[date] = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._selected = selected_date or date.today()
        self._viewing = date(self._selected.year, self._selected.month, 1)
        self._highlight_dates = highlight_dates or []

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        main_layout.setSpacing(SPACING.sm)

        # Navigation
        nav = CalendarNavigation(
            self._viewing.strftime("%B %Y"),
            colors=self._colors
        )
        nav.prev_clicked.connect(self._prev_month)
        nav.next_clicked.connect(self._next_month)
        main_layout.addWidget(nav)
        self._nav = nav

        # Day headers
        headers = QHBoxLayout()
        headers.setSpacing(0)
        for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
            lbl = QLabel(day)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(32, 24)
            lbl.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            headers.addWidget(lbl)
        main_layout.addLayout(headers)

        # Days grid
        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(2)
        main_layout.addWidget(self._grid_container)

        self._build_calendar()

    def _build_calendar(self):
        # Clear existing
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Calculate first day of month
        first_day = self._viewing
        # Find Sunday before first day
        start = first_day - timedelta(days=first_day.weekday() + 1)
        if first_day.weekday() == 6:
            start = first_day

        current = start
        for week in range(6):
            for day in range(7):
                day_widget = CalendarDay(
                    current,
                    is_current_month=(current.month == self._viewing.month),
                    is_selected=(current == self._selected),
                    is_today=(current == date.today()),
                    is_highlighted=(current in self._highlight_dates),
                    colors=self._colors
                )
                day_widget.clicked.connect(lambda d=current: self._select_date(d))
                self._grid.addWidget(day_widget, week, day)
                current += timedelta(days=1)

    def _prev_month(self):
        if self._viewing.month == 1:
            self._viewing = date(self._viewing.year - 1, 12, 1)
        else:
            self._viewing = date(self._viewing.year, self._viewing.month - 1, 1)
        self._nav.set_title(self._viewing.strftime("%B %Y"))
        self._build_calendar()

    def _next_month(self):
        if self._viewing.month == 12:
            self._viewing = date(self._viewing.year + 1, 1, 1)
        else:
            self._viewing = date(self._viewing.year, self._viewing.month + 1, 1)
        self._nav.set_title(self._viewing.strftime("%B %Y"))
        self._build_calendar()

    def _select_date(self, d: date):
        self._selected = d
        self._build_calendar()
        self.date_selected.emit(d)

    def set_date(self, d: date):
        self._selected = d
        self._viewing = date(d.year, d.month, 1)
        self._nav.set_title(self._viewing.strftime("%B %Y"))
        self._build_calendar()

    def set_highlights(self, dates: List[date]):
        self._highlight_dates = dates
        self._build_calendar()


class CalendarDay(QPushButton):
    """
    Individual calendar day button.

    Usage:
        day = CalendarDay(date(2024, 1, 15), is_selected=True)
        day.clicked.connect(self.select_day)
    """

    def __init__(
        self,
        day_date: date,
        is_current_month: bool = True,
        is_selected: bool = False,
        is_today: bool = False,
        is_highlighted: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(str(day_date.day), parent)
        self._colors = colors or get_theme("dark")
        self._date = day_date

        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Determine style
        if is_selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        elif is_today:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.primary};
                    border: 2px solid {self._colors.primary};
                    border-radius: 16px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{
                    background-color: {self._colors.primary}26;
                }}
            """)
        elif is_highlighted:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary}26;
                    color: {self._colors.text_primary if is_current_month else self._colors.text_disabled};
                    border: none;
                    border-radius: 16px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.primary}40;
                }}
            """)
        else:
            text_color = self._colors.text_primary if is_current_month else self._colors.text_disabled
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_color};
                    border: none;
                    border-radius: 16px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)


class CalendarNavigation(QFrame):
    """
    Month/year navigation for calendar.

    Usage:
        nav = CalendarNavigation("January 2024")
        nav.prev_clicked.connect(self.prev_month)
        nav.next_clicked.connect(self.next_month)
    """

    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    title_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Previous button
        prev_btn = QPushButton("‹")
        prev_btn.setFixedSize(28, 28)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: 14px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)
        prev_btn.clicked.connect(self.prev_clicked.emit)
        layout.addWidget(prev_btn)

        # Title
        self._title = QPushButton(title)
        self._title.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                color: {self._colors.primary};
            }}
        """)
        self._title.clicked.connect(self.title_clicked.emit)
        layout.addWidget(self._title, 1)

        # Next button
        next_btn = QPushButton("›")
        next_btn.setFixedSize(28, 28)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: 14px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)
        next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(next_btn)

    def set_title(self, title: str):
        self._title.setText(title)


class DateRangePicker(QFrame):
    """
    Date range picker with start and end dates.

    Usage:
        picker = DateRangePicker()
        picker.range_changed.connect(self.filter_by_dates)
    """

    range_changed = pyqtSignal(object, object)  # start_date, end_date

    def __init__(
        self,
        start_date: date = None,
        end_date: date = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._start = start_date
        self._end = end_date

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Start date
        self._start_btn = QPushButton(self._format_date(start_date) or "Start date")
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_date_btn(self._start_btn, start_date is not None)
        layout.addWidget(self._start_btn)

        # Arrow
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {self._colors.text_secondary};")
        layout.addWidget(arrow)

        # End date
        self._end_btn = QPushButton(self._format_date(end_date) or "End date")
        self._end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_date_btn(self._end_btn, end_date is not None)
        layout.addWidget(self._end_btn)

    def _format_date(self, d: date) -> Optional[str]:
        if d:
            return d.strftime("%b %d, %Y")
        return None

    def _style_date_btn(self, btn: QPushButton, has_value: bool):
        if has_value:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_primary};
                    border: none;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    color: {self._colors.primary};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_disabled};
                    border: none;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    color: {self._colors.text_secondary};
                }}
            """)

    def set_range(self, start: date, end: date):
        self._start = start
        self._end = end
        self._start_btn.setText(self._format_date(start) or "Start date")
        self._end_btn.setText(self._format_date(end) or "End date")
        self._style_date_btn(self._start_btn, start is not None)
        self._style_date_btn(self._end_btn, end is not None)
        self.range_changed.emit(start, end)


class QuickDateSelect(QFrame):
    """
    Quick date selection presets.

    Usage:
        quick = QuickDateSelect()
        quick.date_selected.connect(self.apply_preset)
    """

    preset_selected = pyqtSignal(str)  # preset_id

    PRESETS = [
        ("today", "Today"),
        ("yesterday", "Yesterday"),
        ("last_7", "Last 7 days"),
        ("last_30", "Last 30 days"),
        ("this_month", "This month"),
        ("last_month", "Last month"),
    ]

    def __init__(
        self,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        for preset_id, label in self.PRESETS:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_primary};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {SPACING.sm}px {SPACING.md}px;
                    text-align: left;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)
            btn.clicked.connect(lambda checked, p=preset_id: self._select(p))
            layout.addWidget(btn)

    def _select(self, preset_id: str):
        self._selected = preset_id
        self.preset_selected.emit(preset_id)

    def get_date_range(self, preset_id: str):
        """Convert preset to actual date range"""
        today = date.today()

        if preset_id == "today":
            return today, today
        elif preset_id == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif preset_id == "last_7":
            return today - timedelta(days=7), today
        elif preset_id == "last_30":
            return today - timedelta(days=30), today
        elif preset_id == "this_month":
            start = date(today.year, today.month, 1)
            return start, today
        elif preset_id == "last_month":
            first_this = date(today.year, today.month, 1)
            last_month_end = first_this - timedelta(days=1)
            last_month_start = date(last_month_end.year, last_month_end.month, 1)
            return last_month_start, last_month_end

        return None, None
