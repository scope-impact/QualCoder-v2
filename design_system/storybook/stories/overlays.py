"""
Overlays and Layout component stories: modals, toasts, contextmenu, panels, toolbar
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ...components import Button
from ...context_menu import ContextMenuItemWidget
from ...layout import Panel, PanelHeader, Sidebar, StatusBar, Toolbar
from ...modal import ModalBody, ModalFooter, ModalHeader
from ...navigation import NavList
from ...toast import Toast
from ...tokens import RADIUS, SPACING, ColorPalette
from ..page import StoryPage


def create_modals_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Modal preview (static representation)
    modal_preview = QFrame()
    modal_preview.setStyleSheet(f"""
        QFrame {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: {RADIUS.lg}px;
        }}
    """)
    modal_preview.setFixedSize(400, 250)

    modal_layout = QVBoxLayout(modal_preview)
    modal_layout.setContentsMargins(0, 0, 0, 0)
    modal_layout.setSpacing(0)

    # Header
    header = ModalHeader("Confirm Action", colors=colors)
    modal_layout.addWidget(header)

    # Body
    body = ModalBody(colors=colors)
    body_label = QLabel(
        "Are you sure you want to delete this item?\nThis action cannot be undone."
    )
    body_label.setStyleSheet(f"color: {colors.text_secondary}; font-size: 14px;")
    body_label.setWordWrap(True)
    body.layout().addWidget(body_label)
    modal_layout.addWidget(body, 1)

    # Footer
    footer = ModalFooter(colors=colors)
    cancel_btn = Button("Cancel", variant="ghost", colors=colors)
    delete_btn = Button("Delete", variant="danger", colors=colors)
    footer.layout().addStretch()
    footer.layout().addWidget(cancel_btn)
    footer.layout().addWidget(delete_btn)
    modal_layout.addWidget(footer)

    examples.append(
        (
            "Modal Dialog",
            modal_preview,
            'modal = Modal(title="Confirm")\nmodal.add_content(widget)\nmodal.show()',
        )
    )

    return StoryPage(
        "Modals",
        "Modal dialogs for confirmations, forms, and focused interactions.",
        examples,
        colors=colors,
    )


def create_toasts_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Toast variants
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setSpacing(SPACING.sm)

    for variant in ["info", "success", "warning", "error"]:
        toast = Toast(
            message=f"This is a {variant} notification", variant=variant, colors=colors
        )
        layout.addWidget(toast)

    examples.append(
        ("Toast Variants", container, 'Toast(message="Success!", variant="success")')
    )

    return StoryPage(
        "Toasts",
        "Toast notifications for non-blocking feedback messages.",
        examples,
        colors=colors,
    )


def create_contextmenu_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Context menu preview
    menu = QFrame()
    menu.setStyleSheet(f"""
        QFrame {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: {RADIUS.md}px;
        }}
    """)
    menu.setFixedWidth(200)

    menu_layout = QVBoxLayout(menu)
    menu_layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
    menu_layout.setSpacing(0)

    items = [
        ("mdi6.content-cut", "Cut"),
        ("mdi6.content-copy", "Copy"),
        ("mdi6.content-paste", "Paste"),
        None,  # Separator
        ("mdi6.delete", "Delete"),
    ]

    for item in items:
        if item is None:
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {colors.border};")
            menu_layout.addWidget(sep)
        else:
            icon, text = item
            item_widget = ContextMenuItemWidget(
                text=text,
                icon=icon,
                variant="danger" if text == "Delete" else "default",
                colors=colors,
            )
            menu_layout.addWidget(item_widget)

    examples.append(
        (
            "Context Menu",
            menu,
            'menu = ContextMenu()\nmenu.add_item("Cut", icon="mdi6.content-cut", shortcut="Ctrl+X")',
        )
    )

    return StoryPage(
        "Context Menu",
        "Right-click context menus for contextual actions.",
        examples,
        colors=colors,
    )


def create_panels_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Panel with header
    panel = Panel(colors=colors)
    panel.setFixedSize(350, 200)

    panel_header = PanelHeader(title="Files", colors=colors)
    panel.layout().insertWidget(0, panel_header)

    content = QLabel("Panel content goes here...")
    content.setStyleSheet(f"color: {colors.text_secondary}; padding: 16px;")
    content.setAlignment(Qt.AlignmentFlag.AlignCenter)
    panel.layout().addWidget(content)

    examples.append(
        (
            "Panel with Header",
            panel,
            'panel = Panel()\nheader = PanelHeader(title="Files")',
        )
    )

    # Sidebar
    sidebar = Sidebar(colors=colors)
    sidebar.setFixedSize(220, 200)

    nav = NavList(colors=colors)
    nav.add_section("Main")
    nav.add_item("Dashboard", icon="mdi6.view-dashboard", active=True)
    nav.add_item("Files", icon="mdi6.folder")
    nav.add_item("Codes", icon="mdi6.tag")
    sidebar.layout().addWidget(nav)

    examples.append(
        (
            "Sidebar Navigation",
            sidebar,
            'sidebar = Sidebar()\nnav = NavList()\nnav.add_item("Dashboard", icon="mdi6.view-dashboard")',
        )
    )

    return StoryPage(
        "Panels",
        "Panel and sidebar containers for organizing content.",
        examples,
        colors=colors,
    )


def create_toolbar_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Toolbar with buttons
    toolbar = Toolbar(colors=colors)
    toolbar.setFixedWidth(500)

    # Add tool buttons
    for icon in ["mdi6.folder", "mdi6.content-save", "mdi6.undo", "mdi6.redo"]:
        toolbar.add_button(icon=icon)

    toolbar.add_divider()

    for icon in ["mdi6.content-cut", "mdi6.content-copy", "mdi6.content-paste"]:
        toolbar.add_button(icon=icon)

    examples.append(
        (
            "Toolbar",
            toolbar,
            'toolbar = Toolbar()\ntoolbar.add_button(icon="mdi6.folder")\ntoolbar.add_divider()',
        )
    )

    # Status bar
    status = StatusBar(colors=colors)
    status.setFixedWidth(500)
    status.add_item("Ready", key="status")
    status.add_item("Ln 42, Col 15", align="right")
    status.add_item("UTF-8", align="right")
    status.add_item("Python", align="right")

    examples.append(
        (
            "Status Bar",
            status,
            'status = StatusBar()\nstatus.add_item("Ready", key="status")\nstatus.add_item("UTF-8", align="right")',
        )
    )

    return StoryPage(
        "Toolbar",
        "Toolbar and status bar components for application chrome.",
        examples,
        colors=colors,
    )


def get_stories(
    colors: ColorPalette, layout_only: bool = False
) -> list[tuple[str, str, StoryPage]]:
    """Return overlay or layout stories based on layout_only flag"""
    if layout_only:
        return [
            ("panels", "Panels", create_panels_story(colors)),
            ("toolbar", "Toolbar", create_toolbar_story(colors)),
        ]
    return [
        ("modals", "Modals", create_modals_story(colors)),
        ("toasts", "Toasts", create_toasts_story(colors)),
        ("contextmenu", "Context Menu", create_contextmenu_story(colors)),
    ]
