"""
Storybook main application window
"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from ..tokens import get_colors
from .sidebar import StorybookSidebar
from .page import StoryPage
from .stories import get_all_sections


class Storybook(QMainWindow):
    """Main Storybook application window"""

    def __init__(self):
        super().__init__()
        self._colors = get_colors()
        self._pages = {}
        self._current_page_key = None

        self.setWindowTitle("Design System Storybook")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self._colors.background};
            }}
        """)

        self._build_ui()

    def _build_ui(self):
        """Build or rebuild the entire UI"""
        # Main widget
        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = StorybookSidebar(
            self._on_page_select,
            colors=self._colors
        )
        main_layout.addWidget(self._sidebar)

        # Content
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)

        self.setCentralWidget(main)

        # Add stories
        self._pages = {}
        self._setup_stories()

        # Restore current page if rebuilding
        if self._current_page_key and self._current_page_key in self._pages:
            self._stack.setCurrentWidget(self._pages[self._current_page_key])

    def _on_page_select(self, key: str):
        self._current_page_key = key
        if key in self._pages:
            self._stack.setCurrentWidget(self._pages[key])

    def _add_story(self, key: str, page: StoryPage):
        self._pages[key] = page
        self._stack.addWidget(page)

    def _setup_stories(self):
        """Setup all story sections from the story registry"""
        sections = get_all_sections(self._colors)

        for section_name, stories in sections:
            self._sidebar.add_section(section_name)
            for key, label, page in stories:
                self._sidebar.add_item(key, label)
                self._add_story(key, page)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = Storybook()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
