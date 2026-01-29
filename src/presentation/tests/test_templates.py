"""
Tests for UI Templates

Tests cover:
- AppShell creation and configuration
- Layout templates (Sidebar, ThreePanel, SinglePanel)
- Screen protocol implementation
- Navigation signals
- Slot content management
"""

import pytest
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt


class TestAppShell:
    """Tests for the main AppShell template"""

    def test_app_shell_creation(self, qapp, colors):
        """AppShell should create without errors"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        assert shell is not None
        assert shell.windowTitle() == "QualCoder"

    def test_app_shell_set_project(self, qapp, colors):
        """AppShell should update window title with project name"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        shell.set_project("my_research.qda")

        assert "my_research.qda" in shell.windowTitle()

    def test_app_shell_has_all_components(self, qapp, colors):
        """AppShell should have all required components"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)

        # Check all components exist
        assert shell.toolbar_slot is not None
        assert shell.content_slot is not None
        assert shell.status_bar is not None
        assert shell.menu_bar is not None
        assert shell.tab_bar is not None

    def test_app_shell_menu_signal(self, qapp, colors):
        """AppShell should emit menu_clicked signal"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)

        # Track signal emission
        received_signals = []
        shell.menu_clicked.connect(lambda menu_id: received_signals.append(menu_id))

        # Simulate menu click by calling internal method
        shell.menu_bar._on_click("coding")

        assert "coding" in received_signals

    def test_app_shell_tab_signal(self, qapp, colors):
        """AppShell should emit tab_clicked signal"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)

        received_signals = []
        shell.tab_clicked.connect(lambda tab_id: received_signals.append(tab_id))

        shell.tab_bar._on_click("reports")

        assert "reports" in received_signals

    def test_app_shell_set_active_menu(self, qapp, colors):
        """AppShell should track active menu item"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        shell.set_active_menu("coding")

        assert shell.menu_bar._active_id == "coding"

    def test_app_shell_set_active_tab(self, qapp, colors):
        """AppShell should track active tab"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        shell.set_active_tab("reports")

        assert shell.tab_bar._active_id == "reports"

    def test_app_shell_set_toolbar_content(self, qapp, colors, placeholder_widget):
        """AppShell should accept toolbar content"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        toolbar = placeholder_widget("Toolbar Content")

        shell.set_toolbar_content(toolbar)

        assert shell.toolbar_slot._content is not None

    def test_app_shell_set_content(self, qapp, colors, placeholder_widget):
        """AppShell should accept main content"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        content = placeholder_widget("Main Content")

        shell.set_content(content)

        assert shell.content_slot._content is not None

    def test_app_shell_set_status_message(self, qapp, colors):
        """AppShell should update status bar message"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)
        shell.set_status_message("Processing files...")

        assert shell.status_bar._message_label.text() == "Processing files..."

    def test_app_shell_set_screen(self, qapp, colors):
        """AppShell should accept screen objects implementing ScreenProtocol"""
        from ui.templates import AppShell

        shell = AppShell(colors=colors)

        # Create a mock screen
        class MockScreen:
            def get_toolbar_content(self):
                widget = QWidget()
                return widget

            def get_content(self):
                widget = QWidget()
                widget.setMinimumSize(100, 100)
                return widget

            def get_status_message(self):
                return "Mock Screen Active"

        screen = MockScreen()
        shell.set_screen(screen)

        assert shell.status_bar._message_label.text() == "Mock Screen Active"
        assert shell.toolbar_slot._content is not None
        assert shell.content_slot._content is not None


class TestSidebarLayout:
    """Tests for SidebarLayout"""

    def test_sidebar_layout_creation(self, qapp, colors):
        """SidebarLayout should create without errors"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(colors=colors)
        assert layout is not None

    def test_sidebar_layout_custom_width(self, qapp, colors):
        """SidebarLayout should accept custom sidebar width"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(
            sidebar_width=300,
            sidebar_min=250,
            sidebar_max=450,
            colors=colors
        )

        assert layout._sidebar.minimumWidth() == 250
        assert layout._sidebar.maximumWidth() == 450

    def test_sidebar_layout_set_sidebar(self, qapp, colors, placeholder_widget):
        """SidebarLayout should accept sidebar content"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(colors=colors)
        sidebar_content = placeholder_widget("Sidebar")

        layout.set_sidebar(sidebar_content)

        assert layout._sidebar_layout.count() == 1

    def test_sidebar_layout_set_content(self, qapp, colors, placeholder_widget):
        """SidebarLayout should accept main content"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(colors=colors)
        main_content = placeholder_widget("Main Content")

        layout.set_content(main_content)

        assert layout._main_layout.count() == 1

    def test_sidebar_layout_replace_content(self, qapp, colors, placeholder_widget):
        """SidebarLayout should replace existing content"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(colors=colors)

        # Set initial content
        layout.set_content(placeholder_widget("First"))
        assert layout._main_layout.count() == 1

        # Replace content
        layout.set_content(placeholder_widget("Second"))
        assert layout._main_layout.count() == 1

    def test_sidebar_layout_splitter_access(self, qapp, colors):
        """SidebarLayout should provide splitter access"""
        from ui.templates import SidebarLayout

        layout = SidebarLayout(colors=colors)

        assert layout.splitter is not None
        assert layout.sidebar is not None
        assert layout.main is not None


class TestThreePanelLayout:
    """Tests for ThreePanelLayout"""

    def test_three_panel_creation(self, qapp, colors):
        """ThreePanelLayout should create without errors"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        assert layout is not None

    def test_three_panel_custom_widths(self, qapp, colors):
        """ThreePanelLayout should accept custom panel widths"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(
            left_width=300,
            right_width=250,
            left_min=200,
            left_max=400,
            right_min=150,
            right_max=350,
            colors=colors
        )

        assert layout._left.minimumWidth() == 200
        assert layout._left.maximumWidth() == 400
        assert layout._right.minimumWidth() == 150
        assert layout._right.maximumWidth() == 350

    def test_three_panel_set_left(self, qapp, colors, placeholder_widget):
        """ThreePanelLayout should accept left panel content"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        layout.set_left(placeholder_widget("Left"))

        assert layout._left_layout.count() == 1

    def test_three_panel_set_center(self, qapp, colors, placeholder_widget):
        """ThreePanelLayout should accept center panel content"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        layout.set_center(placeholder_widget("Center"))

        assert layout._center_layout.count() == 1

    def test_three_panel_set_right(self, qapp, colors, placeholder_widget):
        """ThreePanelLayout should accept right panel content"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        layout.set_right(placeholder_widget("Right"))

        assert layout._right_layout.count() == 1

    def test_three_panel_set_all(self, qapp, colors, placeholder_widget):
        """ThreePanelLayout should accept all three panels"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        layout.set_left(placeholder_widget("Left"))
        layout.set_center(placeholder_widget("Center"))
        layout.set_right(placeholder_widget("Right"))

        assert layout._left_layout.count() == 1
        assert layout._center_layout.count() == 1
        assert layout._right_layout.count() == 1

    def test_three_panel_hide_show_panels(self, qapp, colors, placeholder_widget):
        """ThreePanelLayout should hide/show side panels"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)
        layout.set_left(placeholder_widget("Left"))
        layout.set_right(placeholder_widget("Right"))

        # Hide panels - use isHidden() which checks widget's own state
        # (isVisible() requires parent to be visible too)
        layout.hide_left()
        layout.hide_right()

        assert layout._left.isHidden()
        assert layout._right.isHidden()

        # Show panels
        layout.show_left()
        layout.show_right()

        assert not layout._left.isHidden()
        assert not layout._right.isHidden()

    def test_three_panel_accessors(self, qapp, colors):
        """ThreePanelLayout should provide panel accessors"""
        from ui.templates import ThreePanelLayout

        layout = ThreePanelLayout(colors=colors)

        assert layout.left is not None
        assert layout.center is not None
        assert layout.right is not None
        assert layout.splitter is not None


class TestSinglePanelLayout:
    """Tests for SinglePanelLayout"""

    def test_single_panel_creation(self, qapp, colors):
        """SinglePanelLayout should create without errors"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(colors=colors)
        assert layout is not None

    def test_single_panel_with_padding(self, qapp, colors):
        """SinglePanelLayout should apply padding"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(padding=24, colors=colors)

        margins = layout._content_layout.contentsMargins()
        assert margins.left() == 24
        assert margins.right() == 24
        assert margins.top() == 24
        assert margins.bottom() == 24

    def test_single_panel_scrollable(self, qapp, colors):
        """SinglePanelLayout should create scrollable container"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(scrollable=True, colors=colors)

        assert layout._scroll is not None

    def test_single_panel_max_width(self, qapp, colors, placeholder_widget):
        """SinglePanelLayout should respect max width"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(max_width=800, colors=colors)
        content = placeholder_widget("Content")
        layout.set_content(content)

        assert content.maximumWidth() == 800

    def test_single_panel_set_content(self, qapp, colors, placeholder_widget):
        """SinglePanelLayout should accept content"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(colors=colors)
        layout.set_content(placeholder_widget("Content"))

        assert layout._content_layout.count() == 1

    def test_single_panel_replace_content(self, qapp, colors, placeholder_widget):
        """SinglePanelLayout should replace existing content"""
        from ui.templates import SinglePanelLayout

        layout = SinglePanelLayout(colors=colors)

        layout.set_content(placeholder_widget("First"))
        layout.set_content(placeholder_widget("Second"))

        assert layout._content_layout.count() == 1


class TestToolbarSlot:
    """Tests for ToolbarSlot component"""

    def test_toolbar_slot_creation(self, qapp, colors):
        """ToolbarSlot should create without errors"""
        from ui.templates.app_shell import ToolbarSlot

        slot = ToolbarSlot(colors=colors)
        assert slot is not None
        assert slot.minimumHeight() == 52

    def test_toolbar_slot_set_content(self, qapp, colors, placeholder_widget):
        """ToolbarSlot should accept content"""
        from ui.templates.app_shell import ToolbarSlot

        slot = ToolbarSlot(colors=colors)
        content = placeholder_widget("Toolbar")

        slot.set_content(content)

        assert slot._content is not None

    def test_toolbar_slot_clear(self, qapp, colors, placeholder_widget):
        """ToolbarSlot should clear content"""
        from ui.templates.app_shell import ToolbarSlot

        slot = ToolbarSlot(colors=colors)
        slot.set_content(placeholder_widget("Toolbar"))
        slot.clear()

        assert slot._content is None

    def test_toolbar_slot_replace_content(self, qapp, colors, placeholder_widget):
        """ToolbarSlot should replace existing content"""
        from ui.templates.app_shell import ToolbarSlot

        slot = ToolbarSlot(colors=colors)
        slot.set_content(placeholder_widget("First"))
        slot.set_content(placeholder_widget("Second"))

        assert slot._layout.count() == 1


class TestContentSlot:
    """Tests for ContentSlot component"""

    def test_content_slot_creation(self, qapp, colors):
        """ContentSlot should create without errors"""
        from ui.templates.app_shell import ContentSlot

        slot = ContentSlot(colors=colors)
        assert slot is not None

    def test_content_slot_set_content(self, qapp, colors, placeholder_widget):
        """ContentSlot should accept content"""
        from ui.templates.app_shell import ContentSlot

        slot = ContentSlot(colors=colors)
        content = placeholder_widget("Content")

        slot.set_content(content)

        assert slot._content is not None

    def test_content_slot_clear(self, qapp, colors, placeholder_widget):
        """ContentSlot should clear content"""
        from ui.templates.app_shell import ContentSlot

        slot = ContentSlot(colors=colors)
        slot.set_content(placeholder_widget("Content"))
        slot.clear()

        assert slot._content is None


class TestAppMenuBar:
    """Tests for AppMenuBar component"""

    def test_menu_bar_has_all_items(self, qapp, colors):
        """AppMenuBar should have all QualCoder menu items"""
        from ui.templates.app_shell import AppMenuBar, MENU_ITEMS

        menu_bar = AppMenuBar(colors=colors)

        for menu_id, label in MENU_ITEMS:
            assert menu_id in menu_bar._buttons

    def test_menu_bar_signal_emission(self, qapp, colors):
        """AppMenuBar should emit item_clicked signal"""
        from ui.templates.app_shell import AppMenuBar

        menu_bar = AppMenuBar(colors=colors)

        received = []
        menu_bar.item_clicked.connect(lambda x: received.append(x))

        menu_bar._on_click("files")

        assert "files" in received

    def test_menu_bar_active_state(self, qapp, colors):
        """AppMenuBar should track active item"""
        from ui.templates.app_shell import AppMenuBar

        menu_bar = AppMenuBar(colors=colors)
        menu_bar.set_active("reports")

        assert menu_bar._active_id == "reports"


class TestAppTabBar:
    """Tests for AppTabBar component"""

    def test_tab_bar_has_all_tabs(self, qapp, colors):
        """AppTabBar should have all QualCoder tabs"""
        from ui.templates.app_shell import AppTabBar, TAB_ITEMS

        tab_bar = AppTabBar(colors=colors)

        for tab_id, label, icon in TAB_ITEMS:
            assert tab_id in tab_bar._buttons

    def test_tab_bar_signal_emission(self, qapp, colors):
        """AppTabBar should emit tab_clicked signal"""
        from ui.templates.app_shell import AppTabBar

        tab_bar = AppTabBar(colors=colors)

        received = []
        tab_bar.tab_clicked.connect(lambda x: received.append(x))

        tab_bar._on_click("manage")

        assert "manage" in received

    def test_tab_bar_active_state(self, qapp, colors):
        """AppTabBar should track active tab"""
        from ui.templates.app_shell import AppTabBar

        tab_bar = AppTabBar(colors=colors)
        tab_bar.set_active("action_log")

        assert tab_bar._active_id == "action_log"


class TestAppStatusBar:
    """Tests for AppStatusBar component"""

    def test_status_bar_creation(self, qapp, colors):
        """AppStatusBar should create without errors"""
        from ui.templates.app_shell import AppStatusBar

        status_bar = AppStatusBar(colors=colors)
        assert status_bar is not None

    def test_status_bar_set_message(self, qapp, colors):
        """AppStatusBar should update message"""
        from ui.templates.app_shell import AppStatusBar

        status_bar = AppStatusBar(colors=colors)
        status_bar.set_message("Loading...")

        assert status_bar._message_label.text() == "Loading..."

    def test_status_bar_add_stat(self, qapp, colors):
        """AppStatusBar should add stats"""
        from ui.templates.app_shell import AppStatusBar

        status_bar = AppStatusBar(colors=colors)
        status_bar.add_stat("custom", "Custom Stat")

        assert "custom" in status_bar._stats

    def test_status_bar_set_stat(self, qapp, colors):
        """AppStatusBar should update stats"""
        from ui.templates.app_shell import AppStatusBar

        status_bar = AppStatusBar(colors=colors)
        status_bar.set_stat("files", "42 files")

        assert status_bar._stats["files"].text() == "42 files"


class TestScreenIntegration:
    """Integration tests for screens with AppShell"""

    def test_full_screen_integration(self, qapp, colors, placeholder_widget):
        """Full integration test with AppShell and layouts"""
        from ui.templates import AppShell, ThreePanelLayout

        # Create shell
        shell = AppShell(colors=colors)
        shell.set_project("test_project.qda")

        # Create a screen with ThreePanelLayout
        class TestScreen:
            def __init__(self, colors):
                self._colors = colors

            def get_toolbar_content(self):
                toolbar = QWidget()
                layout = QHBoxLayout(toolbar)
                layout.addWidget(QPushButton("Button 1"))
                layout.addWidget(QPushButton("Button 2"))
                layout.addStretch()
                return toolbar

            def get_content(self):
                layout = ThreePanelLayout(colors=self._colors)
                layout.set_left(placeholder_widget("Left Panel"))
                layout.set_center(placeholder_widget("Center Panel"))
                layout.set_right(placeholder_widget("Right Panel"))
                return layout

            def get_status_message(self):
                return "Test Screen | 10 items"

        screen = TestScreen(colors)
        shell.set_screen(screen)

        # Verify integration
        assert shell.status_bar._message_label.text() == "Test Screen | 10 items"
        assert shell.toolbar_slot._content is not None
        assert shell.content_slot._content is not None

    def test_screen_navigation(self, qapp, colors, placeholder_widget):
        """Test navigating between screens"""
        from ui.templates import AppShell, SidebarLayout, SinglePanelLayout

        shell = AppShell(colors=colors)

        class ScreenA:
            def get_toolbar_content(self):
                return None

            def get_content(self):
                return placeholder_widget("Screen A")

            def get_status_message(self):
                return "Screen A"

        class ScreenB:
            def get_toolbar_content(self):
                return placeholder_widget("Toolbar B")

            def get_content(self):
                return placeholder_widget("Screen B")

            def get_status_message(self):
                return "Screen B"

        # Set first screen
        shell.set_screen(ScreenA())
        assert shell.status_bar._message_label.text() == "Screen A"

        # Navigate to second screen
        shell.set_screen(ScreenB())
        assert shell.status_bar._message_label.text() == "Screen B"
        assert shell.toolbar_slot._content is not None
