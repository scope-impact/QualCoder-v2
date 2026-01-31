"""
Folder Tree Widget - Hierarchical Folder Navigation.

Implements QC-027.05 AC #4 (folder structure in source list).

Displays folders in a tree structure with context menu for operations.
Sources can be dragged into folders to organize them.

Usage:
    tree = FolderTree()
    tree.folder_selected.connect(on_folder_selected)
    tree.set_folders(folders)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint


# ============================================================
# Data Types
# ============================================================


@dataclass(frozen=True)
class FolderNode:
    """Represents a folder in the tree."""

    id: str
    name: str
    parent_id: str | None = None
    source_count: int = 0


# ============================================================
# Folder Tree Widget
# ============================================================


class FolderTree(QFrame):
    """
    Tree widget for displaying and navigating folder hierarchy.

    Signals:
        folder_selected: Emitted when a folder is selected (folder_id or None for root)
        create_folder_requested: Emitted when user requests folder creation (parent_id)
        rename_folder_requested: Emitted when user requests folder rename (folder_id)
        delete_folder_requested: Emitted when user requests folder deletion (folder_id)
        move_sources_requested: Emitted when sources are dropped (source_ids, target_folder_id)
    """

    folder_selected = Signal(object)  # FolderNode | None
    create_folder_requested = Signal(object)  # str | None (parent folder id)
    rename_folder_requested = Signal(str)  # folder_id
    delete_folder_requested = Signal(str)  # folder_id
    move_sources_requested = Signal(list, object)  # source_ids, folder_id | None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._folders: list[FolderNode] = []
        self._folder_items: dict[str, QTreeWidgetItem] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the tree widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.setDragDropMode(QTreeWidget.DragDropMode.DropOnly)
        self._tree.setAcceptDrops(True)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        # Configure column
        self._tree.setColumnCount(1)
        self._tree.header().setStretchLastSection(True)

        layout.addWidget(self._tree)

        # Add root item (All Sources)
        self._root_item = QTreeWidgetItem(self._tree, ["All Sources"])
        self._root_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self._root_item.setExpanded(True)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

    def set_folders(self, folders: list[FolderNode]) -> None:
        """
        Set the folder list and rebuild the tree.

        Args:
            folders: List of FolderNode objects
        """
        self._folders = folders
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        """Rebuild the tree from the folder list."""
        # Clear existing children of root
        while self._root_item.childCount() > 0:
            self._root_item.removeChild(self._root_item.child(0))

        self._folder_items.clear()

        # Build folder hierarchy
        # First pass: create all items
        for folder in self._folders:
            item = QTreeWidgetItem()
            item.setText(0, self._format_folder_name(folder))
            item.setData(0, Qt.ItemDataRole.UserRole, folder)
            self._folder_items[folder.id] = item

        # Second pass: establish parent-child relationships
        for folder in self._folders:
            item = self._folder_items[folder.id]
            if folder.parent_id and folder.parent_id in self._folder_items:
                parent_item = self._folder_items[folder.parent_id]
                parent_item.addChild(item)
            else:
                # Add to root
                self._root_item.addChild(item)

        # Expand all by default
        self._tree.expandAll()

    def _format_folder_name(self, folder: FolderNode) -> str:
        """Format folder name with source count."""
        if folder.source_count > 0:
            return f"{folder.name} ({folder.source_count})"
        return folder.name

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        """Handle item click."""
        folder = item.data(0, Qt.ItemDataRole.UserRole)
        self.folder_selected.emit(folder)

    def _show_context_menu(self, position: QPoint) -> None:
        """Show context menu for folder operations."""
        item = self._tree.itemAt(position)
        menu = QMenu(self)

        if item is None or item == self._root_item:
            # Root context menu
            create_action = QAction("New Folder", self)
            create_action.triggered.connect(
                lambda: self.create_folder_requested.emit(None)
            )
            menu.addAction(create_action)
        else:
            folder: FolderNode = item.data(0, Qt.ItemDataRole.UserRole)

            # Folder context menu
            create_action = QAction("New Subfolder", self)
            create_action.triggered.connect(
                lambda: self.create_folder_requested.emit(folder.id)
            )
            menu.addAction(create_action)

            menu.addSeparator()

            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(
                lambda: self.rename_folder_requested.emit(folder.id)
            )
            menu.addAction(rename_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(
                lambda: self.delete_folder_requested.emit(folder.id)
            )
            menu.addAction(delete_action)

        menu.exec(self._tree.mapToGlobal(position))

    def select_folder(self, folder_id: str | None) -> None:
        """
        Programmatically select a folder.

        Args:
            folder_id: Folder ID to select, or None for root
        """
        if folder_id is None:
            self._tree.setCurrentItem(self._root_item)
        elif folder_id in self._folder_items:
            self._tree.setCurrentItem(self._folder_items[folder_id])

    def get_selected_folder(self) -> FolderNode | None:
        """Get the currently selected folder."""
        current = self._tree.currentItem()
        if current and current != self._root_item:
            return current.data(0, Qt.ItemDataRole.UserRole)
        return None

    def refresh_folder(self, folder: FolderNode) -> None:
        """
        Update a single folder's display.

        Args:
            folder: Updated folder data
        """
        if folder.id in self._folder_items:
            item = self._folder_items[folder.id]
            item.setText(0, self._format_folder_name(folder))
            item.setData(0, Qt.ItemDataRole.UserRole, folder)
