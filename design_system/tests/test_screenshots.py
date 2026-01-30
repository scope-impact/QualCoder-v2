"""
Screenshot tests for design system components.
Captures visual snapshots of components for documentation and regression testing.

Run with: pytest test_screenshots.py -v -s
Screenshots saved to: design_system/tests/screenshots/
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel


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
        tabs.add_tab("Overview", active=True)
        tabs.add_tab("Files")
        tabs.add_tab("Codes")
        tabs.add_tab("Reports")

        tabs.setMinimumWidth(500)
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


class TestToggleScreenshots:
    """Capture screenshots of toggle components"""

    def test_toggle_states(self, qtbot, take_screenshot):
        """Screenshot toggle in different states"""
        from design_system.toggle import Toggle, LabeledToggle

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # Simple toggles
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setSpacing(16)

        toggle_off = Toggle()
        toggle_off.setChecked(False)
        row1_layout.addWidget(QLabel("Off:"))
        row1_layout.addWidget(toggle_off)

        toggle_on = Toggle()
        toggle_on.setChecked(True)
        row1_layout.addWidget(QLabel("On:"))
        row1_layout.addWidget(toggle_on)

        layout.addWidget(row1)

        # Labeled toggles
        labeled1 = LabeledToggle(label="Enable notifications")
        labeled1.setChecked(True)
        layout.addWidget(labeled1)

        labeled2 = LabeledToggle(label="Dark mode")
        labeled2.setChecked(False)
        layout.addWidget(labeled2)

        container.setFixedWidth(300)
        qtbot.addWidget(container)
        take_screenshot(container, "toggle_states")


class TestPickerScreenshots:
    """Capture screenshots of picker components"""

    def test_color_picker(self, qtbot, take_screenshot):
        """Screenshot color picker"""
        from design_system.forms import ColorPicker

        picker = ColorPicker()
        picker.setFixedWidth(280)

        qtbot.addWidget(picker)
        take_screenshot(picker, "color_picker")

    def test_date_range_picker(self, qtbot, take_screenshot):
        """Screenshot date range picker"""
        from design_system.date_picker import DateRangePicker

        picker = DateRangePicker()
        picker.setFixedWidth(320)

        qtbot.addWidget(picker)
        take_screenshot(picker, "date_range_picker")


class TestTreeScreenshots:
    """Capture screenshots of tree components"""

    def test_code_tree(self, qtbot, take_screenshot):
        """Screenshot code tree with hierarchy"""
        from design_system.code_tree import CodeTree, CodeItem

        tree = CodeTree()

        # Add hierarchical items
        items = [
            CodeItem(
                id="1",
                name="Themes",
                color="#4CAF50",
                count=25,
                children=[
                    CodeItem(id="1.1", name="Main Theme", color="#66BB6A", count=12),
                    CodeItem(id="1.2", name="Sub Theme", color="#81C784", count=8),
                    CodeItem(id="1.3", name="Minor Theme", color="#A5D6A7", count=5),
                ]
            ),
            CodeItem(
                id="2",
                name="Categories",
                color="#2196F3",
                count=18,
                children=[
                    CodeItem(id="2.1", name="Category A", color="#42A5F5", count=10),
                    CodeItem(id="2.2", name="Category B", color="#64B5F6", count=8),
                ]
            ),
            CodeItem(id="3", name="Uncategorized", color="#FF9800", count=7),
        ]

        tree.set_items(items)
        # Expand parent items to show hierarchy
        tree.expand_item("1", True)
        tree.expand_item("2", True)
        tree.setFixedSize(300, 300)

        qtbot.addWidget(tree)
        take_screenshot(tree, "code_tree")


class TestStatScreenshots:
    """Capture screenshots of statistics components"""

    def test_stat_cards(self, qtbot, take_screenshot):
        """Screenshot stat card variants"""
        from design_system.stat_card import StatCard, MiniStatCard

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # Full stat cards
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setSpacing(12)

        card1 = StatCard(
            value="1,234",
            label="Total Files",
            icon="mdi6.file-multiple",
            trend="+12%",
            trend_direction="up"
        )
        row1_layout.addWidget(card1)

        card2 = StatCard(
            value="567",
            label="Codes Applied",
            icon="mdi6.tag-multiple",
            trend="+8%",
            trend_direction="up"
        )
        row1_layout.addWidget(card2)

        layout.addWidget(row1)

        # Mini stat cards
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setSpacing(8)

        mini1 = MiniStatCard(value="42", label="Memos")
        mini2 = MiniStatCard(value="15", label="Cases")
        mini3 = MiniStatCard(value="8", label="Coders")

        row2_layout.addWidget(mini1)
        row2_layout.addWidget(mini2)
        row2_layout.addWidget(mini3)

        layout.addWidget(row2)

        qtbot.addWidget(container)
        take_screenshot(container, "stat_cards")


class TestUploadScreenshots:
    """Capture screenshots of upload components"""

    def test_drop_zone(self, qtbot, take_screenshot):
        """Screenshot drop zone"""
        from design_system.upload import DropZone

        zone = DropZone(
            accepted_types=[".txt", ".pdf", ".docx", ".mp3", ".mp4"],
            max_files=10
        )
        zone.setFixedSize(400, 200)

        qtbot.addWidget(zone)
        take_screenshot(zone, "drop_zone")


class TestChatScreenshots:
    """Capture screenshots of chat/AI components"""

    def test_message_bubbles(self, qtbot, take_screenshot):
        """Screenshot chat message bubbles"""
        from design_system.chat import MessageBubble

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # User message
        user_msg = MessageBubble(
            text="Can you help me find patterns in the interview data?",
            role="user",
            timestamp="10:30 AM"
        )
        layout.addWidget(user_msg)

        # Assistant message
        assistant_msg = MessageBubble(
            text="I found 3 recurring themes in your data:\n\n1. **Work-life balance** (mentioned 15 times)\n2. **Career growth** (mentioned 12 times)\n3. **Team collaboration** (mentioned 9 times)",
            role="assistant",
            timestamp="10:31 AM"
        )
        layout.addWidget(assistant_msg)

        container.setFixedWidth(450)
        qtbot.addWidget(container)
        take_screenshot(container, "message_bubbles")

    def test_typing_indicator(self, qtbot, take_screenshot):
        """Screenshot typing indicator"""
        from design_system.chat import TypingIndicator

        indicator = TypingIndicator()

        qtbot.addWidget(indicator)
        take_screenshot(indicator, "typing_indicator")

    def test_chat_input(self, qtbot, take_screenshot):
        """Screenshot chat input"""
        from design_system.chat import ChatInput

        chat_input = ChatInput(placeholder="Ask a question about your data...")
        chat_input.setFixedWidth(400)

        qtbot.addWidget(chat_input)
        take_screenshot(chat_input, "chat_input")

    def test_code_suggestion(self, qtbot, take_screenshot):
        """Screenshot AI code suggestion"""
        from design_system.chat import CodeSuggestion

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        suggestion1 = CodeSuggestion(
            code_name="Work-Life Balance",
            color="#4CAF50",
            confidence=0.92
        )
        layout.addWidget(suggestion1)

        suggestion2 = CodeSuggestion(
            code_name="Career Growth",
            color="#2196F3",
            confidence=0.78
        )
        layout.addWidget(suggestion2)

        container.setFixedWidth(400)
        qtbot.addWidget(container)
        take_screenshot(container, "code_suggestions")


class TestEditorScreenshots:
    """Capture screenshots of editor components"""

    def test_code_editor(self, qtbot, take_screenshot):
        """Screenshot code editor with syntax highlighting"""
        from design_system.editors import CodeEditor

        editor = CodeEditor(language="python")
        editor.set_code('''def analyze_codes(data):
    """Analyze qualitative codes in data."""
    themes = {}
    for item in data:
        code = item.get("code")
        if code not in themes:
            themes[code] = 0
        themes[code] += 1
    return themes
''')
        editor.setFixedSize(450, 280)

        qtbot.addWidget(editor)
        take_screenshot(editor, "code_editor")

    def test_rich_text_editor(self, qtbot, take_screenshot):
        """Screenshot rich text editor"""
        from design_system.editors import RichTextEditor

        editor = RichTextEditor()
        editor.set_html("""
        <h3>Research Notes</h3>
        <p>Key findings from the <b>interview session</b>:</p>
        <ul>
            <li>Participant expressed <i>strong feelings</i> about work culture</li>
            <li>Mentioned team dynamics multiple times</li>
        </ul>
        """)
        editor.setFixedSize(400, 250)

        qtbot.addWidget(editor)
        take_screenshot(editor, "rich_text_editor")

    def test_memo_editor(self, qtbot, take_screenshot):
        """Screenshot memo editor"""
        from design_system.editors import MemoEditor

        editor = MemoEditor()
        editor.set_content("This participant showed interesting patterns in their responses about work-life balance. Follow up on the connection to remote work policies.")
        editor.setFixedSize(400, 180)

        qtbot.addWidget(editor)
        take_screenshot(editor, "memo_editor")


class TestModalScreenshots:
    """Capture screenshots of modal/dialog components"""

    def test_modal_dialog(self, qtbot, take_screenshot):
        """Screenshot modal dialog"""
        from design_system.modal import Modal
        from design_system.components import Label

        modal = Modal(title="Confirm Delete", size="sm")
        modal.body.layout().addWidget(
            Label("Are you sure you want to delete this code?\nThis action cannot be undone.")
        )
        modal.add_button("Cancel", variant="outline")
        modal.add_button("Delete", variant="destructive")
        modal.setFixedSize(400, 200)

        qtbot.addWidget(modal)
        take_screenshot(modal, "modal_dialog")

    def test_context_menu(self, qtbot, take_screenshot):
        """Screenshot context menu"""
        from design_system.context_menu import ContextMenu

        # Create a container to show the menu in
        container = QWidget()
        container.setFixedSize(250, 200)

        menu = ContextMenu(parent=container)
        menu.add_item("Edit", icon="mdi6.pencil")
        menu.add_item("Duplicate", icon="mdi6.content-copy")
        menu.add_separator()
        menu.add_item("Move to...", icon="mdi6.folder-move")
        menu.add_separator()
        menu.add_item("Delete", icon="mdi6.delete", variant="danger")

        # Show menu at a position
        menu.popup(container.mapToGlobal(container.rect().center()))

        qtbot.addWidget(container)
        take_screenshot(menu, "context_menu")


class TestLayoutScreenshots:
    """Capture screenshots of layout components"""

    def test_panel(self, qtbot, take_screenshot):
        """Screenshot panel with header"""
        from design_system.layout import Panel, PanelHeader
        from design_system.components import Label

        # Create container to hold header + panel
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Add header
        header = PanelHeader(title="Properties")
        header.add_action("➕", lambda: None)
        header.add_action("⋮", lambda: None)
        container_layout.addWidget(header)

        # Add panel content
        panel = Panel(title="")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(Label("Name: Interview 01"))
        content_layout.addWidget(Label("Type: Text Document"))
        content_layout.addWidget(Label("Size: 24 KB"))
        content_layout.addStretch()
        panel.set_content(content)
        container_layout.addWidget(panel)

        container.setFixedSize(280, 250)

        qtbot.addWidget(container)
        take_screenshot(container, "panel_with_header")

    def test_toolbar(self, qtbot, take_screenshot):
        """Screenshot toolbar with buttons"""
        from design_system.layout import Toolbar

        toolbar = Toolbar()

        # File group - add_group() returns a ToolbarGroup
        file_group = toolbar.add_group()
        file_group.add_button("Open", icon="📂")
        file_group.add_button("Save", icon="💾")

        toolbar.add_divider()

        # Edit group
        edit_group = toolbar.add_group()
        edit_group.add_button("Undo", icon="↩️")
        edit_group.add_button("Redo", icon="↪️")

        toolbar.add_divider()

        # View group
        view_group = toolbar.add_group()
        view_group.add_button("Zoom In", icon="🔍")
        view_group.add_button("Zoom Out", icon="🔎")

        toolbar.setFixedWidth(650)

        qtbot.addWidget(toolbar)
        take_screenshot(toolbar, "toolbar")

    def test_sidebar(self, qtbot, take_screenshot):
        """Screenshot sidebar navigation"""
        from design_system.layout import Sidebar

        sidebar = Sidebar()
        sidebar.add_section("Project")
        sidebar.add_item("Files", icon="📁")
        sidebar.add_item("Codes", icon="🏷️")
        sidebar.add_item("Cases", icon="📂")

        sidebar.add_section("Analysis")
        sidebar.add_item("Reports", icon="📊")
        sidebar.add_item("Queries", icon="🔍")

        sidebar.setFixedSize(220, 300)

        qtbot.addWidget(sidebar)
        take_screenshot(sidebar, "sidebar")


class TestVisualizationScreenshots:
    """Capture screenshots of visualization components"""

    def test_chart_bar(self, qtbot, take_screenshot):
        """Screenshot bar chart"""
        from design_system.charts import ChartWidget, ChartDataPoint

        chart = ChartWidget(title="Code Frequency")
        chart.set_bar_data([
            ChartDataPoint("Theme A", 25, "#4CAF50"),
            ChartDataPoint("Theme B", 18, "#2196F3"),
            ChartDataPoint("Theme C", 12, "#FF9800"),
            ChartDataPoint("Theme D", 8, "#9C27B0"),
        ])
        chart.setFixedSize(400, 300)

        qtbot.addWidget(chart)
        take_screenshot(chart, "chart_bar")

    def test_network_graph(self, qtbot, take_screenshot):
        """Screenshot network graph"""
        from design_system.network_graph import NetworkGraphWidget, GraphNode, GraphEdge

        graph = NetworkGraphWidget()

        # Add nodes
        graph.add_node(GraphNode(id="1", label="Work-Life", color="#4CAF50", size=30))
        graph.add_node(GraphNode(id="2", label="Career", color="#2196F3", size=25))
        graph.add_node(GraphNode(id="3", label="Team", color="#FF9800", size=20))
        graph.add_node(GraphNode(id="4", label="Remote", color="#9C27B0", size=15))

        # Add edges
        graph.add_edge(GraphEdge(source="1", target="2", weight=5))
        graph.add_edge(GraphEdge(source="1", target="3", weight=3))
        graph.add_edge(GraphEdge(source="2", target="3", weight=4))
        graph.add_edge(GraphEdge(source="1", target="4", weight=6))

        graph.layout("spring")
        graph.setFixedSize(400, 350)

        qtbot.addWidget(graph)
        take_screenshot(graph, "network_graph")

    def test_word_cloud(self, qtbot, take_screenshot):
        """Screenshot word cloud"""
        from design_system.word_cloud import WordCloudWidget

        cloud = WordCloudWidget()
        cloud.set_frequencies({
            "qualitative": 50,
            "research": 45,
            "coding": 40,
            "analysis": 35,
            "themes": 30,
            "patterns": 28,
            "interviews": 25,
            "data": 22,
            "findings": 20,
            "methodology": 18,
        })
        # set_frequencies automatically generates the cloud
        cloud.setFixedSize(400, 300)

        qtbot.addWidget(cloud)
        take_screenshot(cloud, "word_cloud")


class TestFilterScreenshots:
    """Capture screenshots of filter components"""

    def test_filter_panel(self, qtbot, take_screenshot):
        """Screenshot filter panel"""
        from design_system.filters import FilterPanel

        panel = FilterPanel()
        panel.add_section("File Type", ["Text", "Audio", "Video", "Image", "PDF"])
        panel.add_section("Status", ["Coded", "Uncoded", "In Progress"])
        panel.add_section("Coder", ["Alice", "Bob", "Charlie"])
        panel.setFixedSize(250, 350)

        qtbot.addWidget(panel)
        take_screenshot(panel, "filter_panel")

    def test_view_toggle(self, qtbot, take_screenshot):
        """Screenshot view toggle"""
        from design_system.filters import ViewToggle

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        toggle1 = ViewToggle(views=["list", "grid", "table"], current="list")
        layout.addWidget(toggle1)

        toggle2 = ViewToggle(views=["day", "week", "month"], current="week")
        layout.addWidget(toggle2)

        qtbot.addWidget(container)
        take_screenshot(container, "view_toggle")


class TestDocumentScreenshots:
    """Capture screenshots of document components"""

    def test_text_panel(self, qtbot, take_screenshot):
        """Screenshot text panel with content"""
        from design_system.document import TextPanel

        panel = TextPanel(
            title="Interview Transcript",
            badge_text="Coded",
            show_line_numbers=True
        )
        panel.set_text("""Interviewer: Thank you for joining us today. Can you tell me about your experience with remote work?

Participant: Sure. I've been working remotely for about two years now. Initially, it was challenging to adjust, but I've grown to appreciate the flexibility it offers.

Interviewer: What aspects of remote work do you find most beneficial?

Participant: I think the biggest benefit is the work-life balance. I can spend more time with my family and avoid the daily commute. It's also easier to focus on deep work without office distractions.""")
        panel.setFixedSize(500, 300)

        qtbot.addWidget(panel)
        take_screenshot(panel, "text_panel")

    def test_transcript_panel(self, qtbot, take_screenshot):
        """Screenshot transcript panel"""
        from design_system.document import TranscriptPanel

        panel = TranscriptPanel()

        # add_segment takes positional args: start_time, end_time, speaker, text
        panel.add_segment(15.0, 25.0, "Interviewer", "Can you describe your typical workday?")
        panel.add_segment(25.0, 65.0, "Participant", "I usually start around 8 AM. I check emails first, then move on to my main tasks for the day.")
        panel.add_segment(65.0, 75.0, "Interviewer", "How do you handle distractions when working from home?")

        panel.setFixedSize(450, 280)

        qtbot.addWidget(panel)
        take_screenshot(panel, "transcript_panel")
