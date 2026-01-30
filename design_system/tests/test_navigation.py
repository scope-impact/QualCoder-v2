"""
Tests for navigation components: TabGroup, Breadcrumb, NavList, StepIndicator, etc.
"""

from PySide6.QtCore import Qt

from design_system.navigation import (
    Breadcrumb,
    MediaTypeSelector,
    MenuItem,
    NavList,
    StepIndicator,
    Tab,
    TabGroup,
)


class TestMenuItem:
    """Tests for MenuItem component"""

    def test_menu_item_creation(self, qtbot):
        """MenuItem should be created with text"""
        item = MenuItem("File")
        qtbot.addWidget(item)

        assert item.text() == "File"

    def test_menu_item_with_icon(self, qtbot):
        """MenuItem should support icon"""
        item = MenuItem("Settings", icon="⚙️")
        qtbot.addWidget(item)

        assert "⚙️" in item.text()

    def test_menu_item_active_state(self, qtbot):
        """MenuItem should support active state"""
        item = MenuItem("File", active=False)
        qtbot.addWidget(item)

        item.setActive(True)
        assert item._active is True

        item.setActive(False)
        assert item._active is False


class TestTab:
    """Tests for Tab component"""

    def test_tab_creation(self, qtbot):
        """Tab should be created with text"""
        tab = Tab("Coding")
        qtbot.addWidget(tab)

        assert "Coding" in tab.text()

    def test_tab_with_icon(self, qtbot):
        """Tab should support icon"""
        tab = Tab("Reports", icon="📊")
        qtbot.addWidget(tab)

        assert "📊" in tab.text()

    def test_tab_active_state(self, qtbot):
        """Tab should support active state"""
        tab = Tab("Test", active=False)
        qtbot.addWidget(tab)

        assert tab.isActive() is False
        tab.setActive(True)
        assert tab.isActive() is True


class TestTabGroup:
    """Tests for TabGroup component"""

    def test_tab_group_creation(self, qtbot):
        """TabGroup should be created"""
        tabs = TabGroup()
        qtbot.addWidget(tabs)

        assert tabs is not None

    def test_tab_group_add_tabs(self, qtbot):
        """TabGroup should add tabs"""
        tabs = TabGroup()
        qtbot.addWidget(tabs)

        tabs.add_tab("Tab 1")
        tabs.add_tab("Tab 2")
        tabs.add_tab("Tab 3")

        assert len(tabs._tabs) == 3

    def test_tab_group_first_tab_active(self, qtbot):
        """TabGroup first tab should be active by default"""
        tabs = TabGroup()
        qtbot.addWidget(tabs)

        tabs.add_tab("Tab 1")
        tabs.add_tab("Tab 2")

        assert tabs.active_tab() == "Tab 1"

    def test_tab_group_signal(self, qtbot):
        """TabGroup should emit tab_changed signal"""
        tabs = TabGroup()
        qtbot.addWidget(tabs)

        tabs.add_tab("Tab 1")
        tab2 = tabs.add_tab("Tab 2")

        with qtbot.waitSignal(tabs.tab_changed, timeout=1000):
            qtbot.mouseClick(tab2, Qt.MouseButton.LeftButton)


class TestBreadcrumb:
    """Tests for Breadcrumb component"""

    def test_breadcrumb_creation(self, qtbot):
        """Breadcrumb should be created"""
        breadcrumb = Breadcrumb()
        qtbot.addWidget(breadcrumb)

        assert breadcrumb is not None

    def test_breadcrumb_set_path(self, qtbot):
        """Breadcrumb should display path"""
        breadcrumb = Breadcrumb()
        qtbot.addWidget(breadcrumb)

        breadcrumb.set_path(["Home", "Projects", "QualCoder"])

        # Should have items in layout
        assert breadcrumb._layout.count() > 0

    def test_breadcrumb_signal(self, qtbot):
        """Breadcrumb should emit item_clicked signal"""
        breadcrumb = Breadcrumb()
        qtbot.addWidget(breadcrumb)

        breadcrumb.set_path(["Home", "Projects", "QualCoder"])

        # Click on first item (should be a button since it's not last)
        with qtbot.waitSignal(breadcrumb.item_clicked, timeout=1000):
            # Find the first button (Home)
            btn = breadcrumb._layout.itemAt(0).widget()
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)


class TestNavList:
    """Tests for NavList component"""

    def test_nav_list_creation(self, qtbot):
        """NavList should be created"""
        nav = NavList()
        qtbot.addWidget(nav)

        assert nav is not None

    def test_nav_list_add_section(self, qtbot):
        """NavList should add sections"""
        nav = NavList()
        qtbot.addWidget(nav)

        nav.add_section("Main")
        # Should have section label
        assert nav._layout.count() > 0

    def test_nav_list_add_item(self, qtbot):
        """NavList should add items"""
        nav = NavList()
        qtbot.addWidget(nav)

        nav.add_item("Dashboard", icon="📊")
        nav.add_item("Settings", icon="⚙️")

        # Should have items
        assert len(nav._items) == 2

    def test_nav_list_signal(self, qtbot):
        """NavList should emit item_clicked signal"""
        nav = NavList()
        qtbot.addWidget(nav)

        btn = nav.add_item("Dashboard")

        with qtbot.waitSignal(nav.item_clicked, timeout=1000):
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)


class TestStepIndicator:
    """Tests for StepIndicator component"""

    def test_step_indicator_creation(self, qtbot):
        """StepIndicator should be created"""
        steps = StepIndicator(["Step 1", "Step 2", "Step 3"])
        qtbot.addWidget(steps)

        assert steps is not None
        assert len(steps._steps) == 3

    def test_step_indicator_current(self, qtbot):
        """StepIndicator should track current step"""
        steps = StepIndicator(["A", "B", "C"], current=1)
        qtbot.addWidget(steps)

        assert steps.current_step() == 1

    def test_step_indicator_set_current(self, qtbot):
        """StepIndicator should update current step"""
        steps = StepIndicator(["A", "B", "C"], current=0)
        qtbot.addWidget(steps)

        steps.set_current(2)
        assert steps.current_step() == 2

    def test_step_indicator_signal(self, qtbot):
        """StepIndicator should emit step_clicked signal when clickable"""
        steps = StepIndicator(["A", "B", "C"], current=1, clickable=True)
        qtbot.addWidget(steps)

        with qtbot.waitSignal(steps.step_clicked, timeout=1000):
            # Click on first step (which should be clickable since current=1)
            step_widget = steps._step_widgets[0]
            # Find the button inside
            circle = step_widget.findChild(
                type(step_widget.layout().itemAt(0).widget())
            )
            qtbot.mouseClick(circle, Qt.MouseButton.LeftButton)


class TestMediaTypeSelector:
    """Tests for MediaTypeSelector component"""

    def test_media_selector_creation(self, qtbot):
        """MediaTypeSelector should be created with options"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
            ]
        )
        qtbot.addWidget(selector)

        assert selector is not None
        assert len(selector._buttons) == 2

    def test_media_selector_default_selection(self, qtbot):
        """MediaTypeSelector should select first option by default"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
            ]
        )
        qtbot.addWidget(selector)

        assert selector.selected() == "text"

    def test_media_selector_initial_selection(self, qtbot):
        """MediaTypeSelector should accept initial selection"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
            ],
            selected="image",
        )
        qtbot.addWidget(selector)

        assert selector.selected() == "image"

    def test_media_selector_set_selected(self, qtbot):
        """MediaTypeSelector should change selection programmatically"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
            ]
        )
        qtbot.addWidget(selector)

        selector.set_selected("image")
        assert selector.selected() == "image"

    def test_media_selector_signal(self, qtbot):
        """MediaTypeSelector should emit selection_changed signal"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
            ]
        )
        qtbot.addWidget(selector)

        # Signal should exist
        assert hasattr(selector, "selection_changed")

    def test_media_selector_all_types(self, qtbot):
        """MediaTypeSelector should work with all coding media types"""
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
                ("av", "A/V", "mdi6.video"),
                ("pdf", "PDF", "mdi6.file-pdf-box"),
            ]
        )
        qtbot.addWidget(selector)

        assert len(selector._buttons) == 4
        assert "text" in selector._buttons
        assert "image" in selector._buttons
        assert "av" in selector._buttons
        assert "pdf" in selector._buttons
