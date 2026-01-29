"""
Screenshot tests for design system components.
Captures visual snapshots of components for documentation and regression testing.

Run with: pytest test_screenshots.py -v -s
Screenshots saved to: design_system/tests/screenshots/
"""

import pytest
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class TestComponentScreenshots:
    """Capture screenshots of all component variants"""

    def test_button_variants(self, qtbot, take_screenshot):
        """Screenshot all button variants"""
        from design_system.components import Button

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        variants = ["primary", "secondary", "outline", "ghost", "destructive"]
        for variant in variants:
            btn = Button(f"{variant.title()} Button", variant=variant)
            layout.addWidget(btn)

        container.setFixedWidth(250)
        qtbot.addWidget(container)
        take_screenshot(container, "buttons_all_variants")

    def test_button_sizes(self, qtbot, take_screenshot):
        """Screenshot all button sizes"""
        from design_system.components import Button

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        sizes = ["sm", "md", "lg"]
        for size in sizes:
            btn = Button(f"{size.upper()}", variant="primary", size=size)
            layout.addWidget(btn)

        qtbot.addWidget(container)
        take_screenshot(container, "buttons_all_sizes")

    def test_input_states(self, qtbot, take_screenshot):
        """Screenshot input field states"""
        from design_system.components import Input

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Normal input
        normal = Input(placeholder="Normal input")
        layout.addWidget(normal)

        # With text
        with_text = Input(placeholder="With text")
        with_text.setText("Hello World")
        layout.addWidget(with_text)

        # Error state
        error = Input(placeholder="Error state")
        error.set_error(True)
        layout.addWidget(error)

        container.setFixedWidth(300)
        qtbot.addWidget(container)
        take_screenshot(container, "inputs_all_states")

    def test_badges(self, qtbot, take_screenshot):
        """Screenshot badge variants"""
        from design_system.components import Badge

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(8)

        variants = ["default", "success", "warning", "error", "info"]
        for variant in variants:
            badge = Badge(variant.title(), variant=variant)
            layout.addWidget(badge)

        qtbot.addWidget(container)
        take_screenshot(container, "badges_all_variants")

    def test_alerts(self, qtbot, take_screenshot):
        """Screenshot alert variants"""
        from design_system.components import Alert

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        alerts_data = [
            ("info", "Information", "This is an informational message."),
            ("success", "Success", "Operation completed successfully!"),
            ("warning", "Warning", "Please review before continuing."),
            ("destructive", "Error", "An error occurred. Please try again."),
        ]

        for variant, title, description in alerts_data:
            alert = Alert(title=title, description=description, variant=variant)
            layout.addWidget(alert)

        container.setFixedWidth(400)
        qtbot.addWidget(container)
        take_screenshot(container, "alerts_all_variants")

    def test_cards(self, qtbot, take_screenshot):
        """Screenshot card component"""
        from design_system.components import Card, Label

        card = Card()
        layout = card.layout()

        title = Label("Card Title", variant="title")
        layout.addWidget(title)

        desc = Label("This is a card component with some content inside.")
        layout.addWidget(desc)

        card.setFixedWidth(300)
        qtbot.addWidget(card)
        take_screenshot(card, "card_basic")

    def test_avatar_sizes(self, qtbot, take_screenshot):
        """Screenshot avatar sizes"""
        from design_system.components import Avatar

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sizes = [24, 32, 40, 48, 64]
        for size in sizes:
            avatar = Avatar(text="JD", size=size)
            layout.addWidget(avatar)

        qtbot.addWidget(container)
        take_screenshot(container, "avatars_all_sizes")

    def test_chips(self, qtbot, take_screenshot):
        """Screenshot chip variants"""
        from design_system.components import Chip

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(8)

        labels = ["Python", "JavaScript", "TypeScript", "Rust"]
        for label in labels:
            chip = Chip(label, closable=True)
            layout.addWidget(chip)

        qtbot.addWidget(container)
        take_screenshot(container, "chips_closable")

    def test_file_icons(self, qtbot, take_screenshot):
        """Screenshot file icons"""
        from design_system.components import FileIcon

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(16)

        types = ["text", "audio", "video", "image", "pdf"]
        for file_type in types:
            icon = FileIcon(file_type=file_type, size=48)
            layout.addWidget(icon)

        qtbot.addWidget(container)
        take_screenshot(container, "file_icons_all_types")

    def test_progress_bars(self, qtbot, take_screenshot):
        """Screenshot progress bar states"""
        from design_system.progress_bar import ProgressBar

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        values = [25, 50, 75, 100]
        for value in values:
            progress = ProgressBar(value=value, show_percentage=True)
            layout.addWidget(progress)

        container.setFixedWidth(300)
        qtbot.addWidget(container)
        take_screenshot(container, "progress_bars_values")

    def test_spinner(self, qtbot, take_screenshot):
        """Screenshot spinner/loading indicator"""
        from design_system.spinner import Spinner, LoadingIndicator

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        spinner = Spinner(size=48)
        layout.addWidget(spinner)

        indicator = LoadingIndicator(text="Loading data...")
        layout.addWidget(indicator)

        qtbot.addWidget(container)
        take_screenshot(container, "loading_indicators")

    def test_toast_variants(self, qtbot, take_screenshot):
        """Screenshot toast variants"""
        from design_system.toast import Toast

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        variants = [
            ("info", "This is an informational message"),
            ("success", "Operation completed successfully"),
            ("warning", "Please check your input"),
            ("error", "Something went wrong"),
        ]

        for variant, message in variants:
            toast = Toast(message=message, variant=variant, duration=0)
            layout.addWidget(toast)

        container.setFixedWidth(400)
        qtbot.addWidget(container)
        take_screenshot(container, "toasts_all_variants")


class TestFormScreenshots:
    """Capture screenshots of form components"""

    def test_search_box(self, qtbot, take_screenshot):
        """Screenshot search box"""
        from design_system.forms import SearchBox

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Empty
        empty = SearchBox(placeholder="Search files...")
        layout.addWidget(empty)

        # With text
        with_text = SearchBox(placeholder="Search...")
        with_text._input.setText("qualitative research")
        layout.addWidget(with_text)

        container.setFixedWidth(300)
        qtbot.addWidget(container)
        take_screenshot(container, "search_box_states")

    def test_select_dropdown(self, qtbot, take_screenshot):
        """Screenshot select component"""
        from design_system.forms import Select

        select = Select(placeholder="Select an option")
        select.add_items(["Option 1", "Option 2", "Option 3"])
        select.setFixedWidth(250)

        qtbot.addWidget(select)
        take_screenshot(select, "select_dropdown")

    def test_textarea(self, qtbot, take_screenshot):
        """Screenshot textarea"""
        from design_system.forms import Textarea

        textarea = Textarea(placeholder="Enter your notes here...")
        textarea.setText("This is a multi-line text area component.\n\nIt supports multiple lines of text input.")
        textarea.setFixedSize(350, 120)

        qtbot.addWidget(textarea)
        take_screenshot(textarea, "textarea_with_content")

    def test_form_group(self, qtbot, take_screenshot):
        """Screenshot form group with label"""
        from design_system.forms import FormGroup
        from design_system.components import Input

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # Required field
        group1 = FormGroup(label="Email Address", required=True)
        input1 = Input(placeholder="you@example.com")
        group1.set_input(input1)
        layout.addWidget(group1)

        # With hint
        group2 = FormGroup(label="Password", hint="Must be at least 8 characters")
        input2 = Input(placeholder="Enter password")
        group2.set_input(input2)
        layout.addWidget(group2)

        container.setFixedWidth(300)
        qtbot.addWidget(container)
        take_screenshot(container, "form_groups")


class TestNavigationScreenshots:
    """Capture screenshots of navigation components"""

    def test_tabs(self, qtbot, take_screenshot):
        """Screenshot tab group"""
        from design_system.navigation import TabGroup

        tabs = TabGroup()
        tabs.add_tab("Overview", "overview")
        tabs.add_tab("Files", "files")
        tabs.add_tab("Codes", "codes")
        tabs.add_tab("Reports", "reports")

        qtbot.addWidget(tabs)
        take_screenshot(tabs, "tab_group")

    def test_breadcrumb(self, qtbot, take_screenshot):
        """Screenshot breadcrumb"""
        from design_system.navigation import Breadcrumb

        breadcrumb = Breadcrumb()
        breadcrumb.set_path(["Home", "Projects", "Research Study", "Files"])

        qtbot.addWidget(breadcrumb)
        take_screenshot(breadcrumb, "breadcrumb_navigation")

    def test_step_indicator(self, qtbot, take_screenshot):
        """Screenshot step indicator"""
        from design_system.navigation import StepIndicator

        steps = StepIndicator(
            steps=["Upload", "Configure", "Process", "Review"],
            current=2
        )

        qtbot.addWidget(steps)
        take_screenshot(steps, "step_indicator")


class TestDataDisplayScreenshots:
    """Capture screenshots of data display components"""

    def test_data_table(self, qtbot, take_screenshot):
        """Screenshot data table"""
        from design_system.data_display import DataTable

        table = DataTable(columns=["Name", "Type", "Size", "Modified"])
        table.set_data([
            {"Name": "interview_01.txt", "Type": "Text", "Size": "24 KB", "Modified": "2024-01-15"},
            {"Name": "audio_session.mp3", "Type": "Audio", "Size": "15 MB", "Modified": "2024-01-14"},
            {"Name": "notes.pdf", "Type": "PDF", "Size": "2.3 MB", "Modified": "2024-01-13"},
        ])
        table.setFixedSize(500, 200)

        qtbot.addWidget(table)
        take_screenshot(table, "data_table")

    def test_empty_state(self, qtbot, take_screenshot):
        """Screenshot empty state"""
        from design_system.data_display import EmptyState

        empty = EmptyState(
            icon="📁",
            title="No files yet",
            message="Upload your first file to get started with your research project.",
            action_text="Upload Files"
        )
        empty.setFixedWidth(400)

        qtbot.addWidget(empty)
        take_screenshot(empty, "empty_state")

    def test_key_value_list(self, qtbot, take_screenshot):
        """Screenshot key-value list"""
        from design_system.data_display import KeyValueList

        kvlist = KeyValueList()
        kvlist.add_item("Project Name", "Qualitative Research Study")
        kvlist.add_item("Created", "January 15, 2024")
        kvlist.add_item("Files", "24")
        kvlist.add_separator()
        kvlist.add_item("Codes", "156")
        kvlist.add_item("Memos", "42")
        kvlist.setFixedWidth(300)

        qtbot.addWidget(kvlist)
        take_screenshot(kvlist, "key_value_list")


class TestMediaScreenshots:
    """Capture screenshots of media components"""

    def test_player_controls(self, qtbot, take_screenshot):
        """Screenshot player controls"""
        from design_system.media import PlayerControls

        controls = PlayerControls()
        controls.setFixedWidth(400)

        qtbot.addWidget(controls)
        take_screenshot(controls, "player_controls")

    def test_timeline(self, qtbot, take_screenshot):
        """Screenshot timeline with segments"""
        from design_system.media import Timeline

        timeline = Timeline(duration=120.0)
        timeline.set_position(45.0)
        timeline.add_segment(10.0, 25.0, "#4CAF50", "Intro")
        timeline.add_segment(30.0, 60.0, "#2196F3", "Main Content")
        timeline.add_segment(80.0, 100.0, "#FF9800", "Conclusion")
        timeline.setFixedWidth(500)

        qtbot.addWidget(timeline)
        take_screenshot(timeline, "timeline_with_segments")


class TestPaginationScreenshots:
    """Capture screenshots of pagination components"""

    def test_pagination(self, qtbot, take_screenshot):
        """Screenshot pagination"""
        from design_system.pagination import Pagination

        pagination = Pagination(total_pages=10, current_page=5)

        qtbot.addWidget(pagination)
        take_screenshot(pagination, "pagination")

    def test_simple_pagination(self, qtbot, take_screenshot):
        """Screenshot simple pagination"""
        from design_system.pagination import SimplePagination

        pagination = SimplePagination(current=3, total=10)

        qtbot.addWidget(pagination)
        take_screenshot(pagination, "simple_pagination")


class TestListScreenshots:
    """Capture screenshots of list components"""

    def test_file_list(self, qtbot, take_screenshot):
        """Screenshot file list"""
        from design_system.lists import FileList

        lst = FileList()
        lst.add_file("1", "interview_transcript.txt", "text", "45 KB")
        lst.add_file("2", "focus_group_audio.mp3", "audio", "23 MB")
        lst.add_file("3", "survey_results.pdf", "pdf", "1.2 MB")
        lst.add_file("4", "participant_photo.jpg", "image", "3.4 MB")
        lst.setFixedSize(350, 250)

        qtbot.addWidget(lst)
        take_screenshot(lst, "file_list")

    def test_case_list(self, qtbot, take_screenshot):
        """Screenshot case list"""
        from design_system.lists import CaseList

        lst = CaseList()
        lst.add_case("1", "Participant 01", "5 files", color="#4CAF50")
        lst.add_case("2", "Participant 02", "3 files", color="#2196F3")
        lst.add_case("3", "Participant 03", "8 files", color="#FF9800")
        lst.setFixedSize(300, 200)

        qtbot.addWidget(lst)
        take_screenshot(lst, "case_list")
