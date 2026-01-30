"""
Upload components
File upload zones, drag-and-drop areas, and file type badges
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors


class DropZone(QFrame):
    """
    Drag-and-drop file upload zone.

    Usage:
        drop = DropZone(accepted_types=["text", "audio", "video"])
        drop.files_dropped.connect(self.handle_files)
    """

    files_dropped = Signal(list)  # list of file paths
    browse_clicked = Signal()

    def __init__(
        self,
        accepted_types: List[str] = None,
        max_files: int = None,
        max_size_mb: int = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._accepted_types = accepted_types or ["text", "audio", "video", "image", "pdf"]
        self._max_files = max_files
        self._max_size_mb = max_size_mb
        self._dragging = False

        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xxl, SPACING.xxl, SPACING.xxl, SPACING.xxl)
        layout.setSpacing(SPACING.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon = QLabel("📁")
        icon.setStyleSheet(f"font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Main text
        main_text = QLabel("Drag and drop files here")
        main_text.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_text)

        # Or browse
        or_layout = QHBoxLayout()
        or_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        or_label = QLabel("or")
        or_label.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_sm}px;")
        or_layout.addWidget(or_label)

        browse_btn = QPushButton("browse files")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.primary};
                border: none;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        browse_btn.clicked.connect(self.browse_clicked.emit)
        or_layout.addWidget(browse_btn)

        layout.addLayout(or_layout)

        # File type badges
        if self._accepted_types:
            badges = FileTypeBadges(self._accepted_types, colors=self._colors)
            layout.addWidget(badges)

        # Constraints info
        constraints = []
        if max_files:
            constraints.append(f"Max {max_files} files")
        if max_size_mb:
            constraints.append(f"Max {max_size_mb}MB each")

        if constraints:
            info = QLabel(" • ".join(constraints))
            info.setStyleSheet(f"""
                color: {self._colors.text_disabled};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info)

    def _update_style(self):
        if self._dragging:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.primary}15;
                    border: 2px dashed {self._colors.primary};
                    border-radius: {RADIUS.lg}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border: 2px dashed {self._colors.border};
                    border-radius: {RADIUS.lg}px;
                }}
                QFrame:hover {{
                    border-color: {self._colors.primary};
                }}
            """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._dragging = True
            self._update_style()

    def dragLeaveEvent(self, event):
        self._dragging = False
        self._update_style()

    def dropEvent(self, event):
        self._dragging = False
        self._update_style()

        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())

        if files:
            self.files_dropped.emit(files)


class FileTypeBadges(QFrame):
    """
    Display accepted file type badges.

    Usage:
        badges = FileTypeBadges(["text", "audio", "video"])
    """

    def __init__(
        self,
        file_types: List[str],
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        type_config = {
            "text": ("📄", "Text", self._colors.file_text),
            "audio": ("🎵", "Audio", self._colors.file_audio),
            "video": ("🎬", "Video", self._colors.file_video),
            "image": ("🖼️", "Image", self._colors.file_image),
            "pdf": ("📕", "PDF", self._colors.file_pdf),
        }

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for file_type in file_types:
            if file_type in type_config:
                icon, label, color = type_config[file_type]
                badge = FileTypeBadge(icon, label, color, colors=self._colors)
                layout.addWidget(badge)


class FileTypeBadge(QFrame):
    """Individual file type badge"""

    def __init__(
        self,
        icon: str,
        label: str,
        color: str,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color}26;
                border-radius: {RADIUS.full}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 12px;")
        layout.addWidget(icon_label)

        text_label = QLabel(label)
        text_label.setStyleSheet(f"""
            color: {color};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(text_label)


class UploadProgress(QFrame):
    """
    File upload progress indicator.

    Usage:
        progress = UploadProgress("document.txt", "12.4 KB")
        progress.set_progress(50)
        progress.cancel_clicked.connect(self.cancel_upload)
    """

    cancel_clicked = Signal()

    def __init__(
        self,
        filename: str,
        file_size: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Header
        header = QHBoxLayout()

        name_label = QLabel(filename)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(name_label)

        if file_size:
            size_label = QLabel(file_size)
            size_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            header.addWidget(size_label)

        header.addStretch()

        # Cancel button
        cancel = QPushButton("×")
        cancel.setFixedSize(20, 20)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {self._colors.error};
            }}
        """)
        cancel.clicked.connect(self.cancel_clicked.emit)
        header.addWidget(cancel)

        layout.addLayout(header)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self._colors.surface_lighter};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self._colors.primary};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._progress)

        # Status
        self._status = QLabel("Uploading...")
        self._status.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(self._status)

    def set_progress(self, value: int):
        self._progress.setValue(value)
        self._status.setText(f"Uploading... {value}%")

    def set_complete(self):
        self._progress.setValue(100)
        self._status.setText("Complete")
        self._status.setStyleSheet(f"""
            color: {self._colors.success};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)

    def set_error(self, message: str = "Upload failed"):
        self._status.setText(message)
        self._status.setStyleSheet(f"""
            color: {self._colors.error};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)


class UploadList(QFrame):
    """
    List of files being uploaded.

    Usage:
        list = UploadList()
        list.add_file("doc1.txt", "12 KB")
        list.add_file("audio.mp3", "5.2 MB")
    """

    file_removed = Signal(str)  # filename

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._items = {}

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.sm)

    def add_file(self, filename: str, file_size: str = "") -> UploadProgress:
        item = UploadProgress(filename, file_size, colors=self._colors)
        item.cancel_clicked.connect(lambda: self._remove(filename))
        self._items[filename] = item
        self._layout.addWidget(item)
        return item

    def _remove(self, filename: str):
        if filename in self._items:
            item = self._items.pop(filename)
            item.deleteLater()
            self.file_removed.emit(filename)

    def update_progress(self, filename: str, progress: int):
        if filename in self._items:
            self._items[filename].set_progress(progress)

    def set_complete(self, filename: str):
        if filename in self._items:
            self._items[filename].set_complete()

    def set_error(self, filename: str, message: str = "Upload failed"):
        if filename in self._items:
            self._items[filename].set_error(message)

    def clear(self):
        for item in self._items.values():
            item.deleteLater()
        self._items = {}


class CompactDropZone(QFrame):
    """
    Compact inline drop zone.

    Usage:
        drop = CompactDropZone("Drop files or click to browse")
        drop.files_dropped.connect(self.handle_files)
    """

    files_dropped = Signal(list)
    browse_clicked = Signal()

    def __init__(
        self,
        text: str = "Drop files or click to browse",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._dragging = False

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        icon = QLabel("📎")
        icon.setStyleSheet(f"font-size: 16px;")
        layout.addWidget(icon)

        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(label, 1)

    def _update_style(self):
        if self._dragging:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.primary}15;
                    border: 1px dashed {self._colors.primary};
                    border-radius: {RADIUS.md}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border: 1px dashed {self._colors.border};
                    border-radius: {RADIUS.md}px;
                }}
                QFrame:hover {{
                    border-color: {self._colors.primary};
                }}
            """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._dragging = True
            self._update_style()

    def dragLeaveEvent(self, event):
        self._dragging = False
        self._update_style()

    def dropEvent(self, event):
        self._dragging = False
        self._update_style()

        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())

        if files:
            self.files_dropped.emit(files)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.browse_clicked.emit()
