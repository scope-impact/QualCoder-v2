"""
List components
File lists, case lists, and other list widgets with staggered animations.
"""

from typing import List, Optional, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import (
    Qt,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QTimer,
    Property,
    QPoint,
)

import qtawesome as qta

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ANIMATION, ColorPalette, get_colors


class AnimatedListItemMixin:
    """
    Mixin to add entrance animations to list items.

    Provides fade-in and slide-in effects with configurable stagger delay.
    """

    def setup_entrance_animation(self, index: int = 0, animate: bool = True):
        """
        Setup entrance animation for this list item.

        Args:
            index: Item index for stagger delay calculation
            animate: Whether to animate (False = instant appearance)
        """
        if not animate:
            return

        # Setup opacity effect for fade-in
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        # Store original position for slide animation
        self._original_pos = None
        self._slide_offset = 20  # pixels to slide from

        # Calculate stagger delay
        stagger_delay = index * ANIMATION.duration_fast  # 100ms between items

        # Use timer to start animation after delay
        QTimer.singleShot(stagger_delay, self._start_entrance_animation)

    def _start_entrance_animation(self):
        """Start the entrance animation."""
        # Fade in animation
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(ANIMATION.duration_normal)  # 200ms
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()


class AnimatedBaseList(QScrollArea):
    """
    Base class for animated list components.

    Items fade in with a stagger effect when added.
    """

    item_clicked = Signal(str)  # item_id
    item_double_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, animate: bool = True, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._items = []
        self._selected = None
        self._animate = animate
        self._item_count = 0

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors.surface};
                border: none;
            }}
        """)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(SPACING.xs)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self._container)

    def _add_item_widget(self, widget):
        """Add item widget with animation setup."""
        if hasattr(widget, 'setup_entrance_animation'):
            widget.setup_entrance_animation(self._item_count, self._animate)
        self._layout.addWidget(widget)
        self._item_count += 1

    def clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items = []
        self._item_count = 0

    def set_selected(self, item_id: str):
        self._selected = item_id
        # Subclasses should override to update visual selection


@dataclass
class ListItem:
    """Generic list item data"""
    id: str
    text: str
    subtitle: str = ""
    icon: str = None
    badge: str = None
    badge_variant: str = "default"
    data: Any = None


class BaseList(QScrollArea):
    """Base class for list components"""

    item_clicked = Signal(str)  # item_id
    item_double_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._items = []
        self._selected = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors.surface};
                border: none;
            }}
        """)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(SPACING.xs)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self._container)

    def clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items = []

    def set_selected(self, item_id: str):
        self._selected = item_id
        # Subclasses should override to update visual selection


class FileList(AnimatedBaseList):
    """
    List of files with type icons and metadata.

    Features entrance animations with stagger effect.

    Usage:
        file_list = FileList()
        file_list.add_file("1", "Interview_01.txt", "text", "12.4 KB")
        file_list.add_file("2", "Focus_group.mp3", "audio", "45.2 MB")
        file_list.item_clicked.connect(self.on_file_click)

        # Disable animations:
        file_list = FileList(animate=False)
    """

    def add_file(
        self,
        id: str,
        name: str,
        file_type: str = "text",
        size: str = "",
        status: str = None
    ):
        item = FileListItem(
            id=id,
            name=name,
            file_type=file_type,
            size=size,
            status=status,
            colors=self._colors
        )
        item.clicked.connect(lambda: self.item_clicked.emit(id))
        item.double_clicked.connect(lambda: self.item_double_clicked.emit(id))
        self._items.append(item)
        self._add_item_widget(item)

    def set_files(self, files: List[dict]):
        self.clear()
        for f in files:
            self.add_file(
                id=f.get("id", ""),
                name=f.get("name", ""),
                file_type=f.get("type", "text"),
                size=f.get("size", ""),
                status=f.get("status")
            )


class FileListItem(QFrame, AnimatedListItemMixin):
    """Individual file list item with entrance animation."""

    clicked = Signal()
    double_clicked = Signal()

    def __init__(
        self,
        id: str,
        name: str,
        file_type: str,
        size: str,
        status: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._id = id

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # File type icon - using qtawesome Material Design icons
        type_config = {
            "text": ("mdi6.file-document-outline", self._colors.file_text),
            "audio": ("mdi6.music-note", self._colors.file_audio),
            "video": ("mdi6.video-outline", self._colors.file_video),
            "image": ("mdi6.image-outline", self._colors.file_image),
            "pdf": ("mdi6.file-pdf-box", self._colors.file_pdf),
        }
        icon_name, color = type_config.get(file_type, ("mdi6.file-outline", self._colors.file_text))

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"background-color: {color}20; border-radius: {RADIUS.sm}px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(20, 20))
        icon_label.setStyleSheet("background: transparent;")
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_frame)

        # Name and size
        info = QVBoxLayout()
        info.setSpacing(2)
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
        info.addWidget(name_label)
        if size:
            size_label = QLabel(size)
            size_label.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
            info.addWidget(size_label)
        layout.addLayout(info, 1)

        # Status badge
        if status:
            badge = QLabel(status)
            badge_colors = {
                "coded": (self._colors.success, f"rgba(76, 175, 80, 0.2)"),
                "pending": (self._colors.text_secondary, self._colors.surface_light),
                "in_progress": (self._colors.warning, f"rgba(255, 152, 0, 0.2)"),
            }
            fg, bg = badge_colors.get(status.lower().replace(" ", "_"), badge_colors["pending"])
            badge.setStyleSheet(f"""
                background-color: {bg};
                color: {fg};
                padding: 2px 8px;
                border-radius: 10px;
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(badge)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()


class CaseList(AnimatedBaseList):
    """
    List of cases/participants with entrance animations.

    Usage:
        case_list = CaseList()
        case_list.add_case("1", "Participant 01", "3 files")
        case_list.item_clicked.connect(self.on_case_click)
    """

    def add_case(
        self,
        id: str,
        name: str,
        subtitle: str = "",
        avatar: str = None,
        color: str = None
    ):
        item = CaseListItem(
            id=id,
            name=name,
            subtitle=subtitle,
            avatar=avatar or name[0].upper(),
            color=color,
            colors=self._colors
        )
        item.clicked.connect(lambda: self.item_clicked.emit(id))
        self._items.append(item)
        self._add_item_widget(item)


class CaseListItem(QFrame, AnimatedListItemMixin):
    """Individual case list item with entrance animation."""

    clicked = Signal()

    def __init__(
        self,
        id: str,
        name: str,
        subtitle: str,
        avatar: str,
        color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Avatar
        avatar_label = QLabel(avatar)
        avatar_label.setFixedSize(36, 36)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg = color or self._colors.primary
        avatar_label.setStyleSheet(f"""
            background-color: {bg};
            color: white;
            border-radius: 18px;
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(avatar_label)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
        info.addWidget(name_label)
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
            info.addWidget(sub_label)
        layout.addLayout(info, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class AttributeList(AnimatedBaseList):
    """
    List of attributes with type indicators and entrance animations.

    Usage:
        attr_list = AttributeList()
        attr_list.add_attribute("1", "Age", "numeric")
        attr_list.add_attribute("2", "Gender", "text")
    """

    def add_attribute(
        self,
        id: str,
        name: str,
        attr_type: str = "text",
        on_edit=None,
        on_delete=None
    ):
        item = AttributeListItem(
            id=id,
            name=name,
            attr_type=attr_type,
            on_edit=on_edit,
            on_delete=on_delete,
            colors=self._colors
        )
        item.clicked.connect(lambda: self.item_clicked.emit(id))
        self._items.append(item)
        self._add_item_widget(item)


class AttributeListItem(QFrame, AnimatedListItemMixin):
    """Individual attribute list item with entrance animation."""

    clicked = Signal()

    def __init__(
        self,
        id: str,
        name: str,
        attr_type: str,
        on_edit=None,
        on_delete=None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Type badge
        type_icon = "🔢" if attr_type == "numeric" else "📝"
        type_label = QLabel(type_icon)
        type_label.setStyleSheet(f"font-size: 16px;")
        layout.addWidget(type_label)

        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
        layout.addWidget(name_label, 1)

        # Type indicator
        type_badge = QLabel(attr_type.capitalize())
        type_badge.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            background-color: {self._colors.surface_light};
            padding: 2px 6px;
            border-radius: 4px;
        """)
        layout.addWidget(type_badge)

        # Actions
        if on_edit:
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(24, 24)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_lighter};
                }}
            """)
            edit_btn.clicked.connect(on_edit)
            layout.addWidget(edit_btn)

        if on_delete:
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(24, 24)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(244, 67, 54, 0.1);
                }}
            """)
            del_btn.clicked.connect(on_delete)
            layout.addWidget(del_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class QueueList(AnimatedBaseList):
    """
    Review queue list with action items and entrance animations.

    Usage:
        queue = QueueList()
        queue.add_item("1", "Create code 'Learning'", "pending", "John")
        queue.item_clicked.connect(self.review_item)
    """

    def add_item(
        self,
        id: str,
        description: str,
        status: str = "pending",
        author: str = ""
    ):
        item = QueueListItem(
            id=id,
            description=description,
            status=status,
            author=author,
            colors=self._colors
        )
        item.clicked.connect(lambda: self.item_clicked.emit(id))
        self._items.append(item)
        self._add_item_widget(item)


class QueueListItem(QFrame, AnimatedListItemMixin):
    """Individual queue list item with entrance animation."""

    clicked = Signal()

    def __init__(
        self,
        id: str,
        description: str,
        status: str,
        author: str,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Status dot
        status_colors = {
            "pending": self._colors.warning,
            "reviewing": self._colors.info,
            "approved": self._colors.success,
            "rejected": self._colors.error,
        }
        dot_color = status_colors.get(status, self._colors.text_secondary)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 4px;")
        layout.addWidget(dot)

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
        layout.addWidget(desc_label, 1)

        # Author
        if author:
            author_label = QLabel(author)
            author_label.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
            layout.addWidget(author_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
