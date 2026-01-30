"""
Image annotation components using QGraphicsScene
For region-based coding on images with rectangle and polygon annotations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from PySide6.QtWidgets import (
    QFrame,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import (
    QPointF,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
# QButtonGroup is now in qt_compat
from PySide6.QtWidgets import QButtonGroup

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors


class AnnotationMode(Enum):
    """Annotation drawing modes"""
    SELECT = "select"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    FREEHAND = "freehand"


@dataclass
class ImageAnnotation:
    """Data class for image annotations"""
    id: str
    annotation_type: str  # "rectangle", "polygon", "freehand"
    points: List[Tuple[float, float]]  # For rect: [(x, y, w, h)], for polygon: [(x1,y1), (x2,y2), ...]
    color: str = "#1E3A5F"  # Prussian ink (from tokens.COLORS_LIGHT.primary)
    label: str = ""
    code_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImageAnnotationLayer(QFrame):
    """
    Image viewer with annotation capabilities.

    Allows drawing rectangles, polygons, and freehand regions
    on images for qualitative coding.

    Usage:
        layer = ImageAnnotationLayer()
        layer.load_image("/path/to/image.jpg")
        layer.set_mode(AnnotationMode.RECTANGLE)

        # Listen for annotations
        layer.annotation_created.connect(on_annotation)
        layer.annotation_selected.connect(on_select)

    Signals:
        annotation_created(annotation): New annotation drawn
        annotation_selected(annotation_id): Annotation clicked
        annotation_deleted(annotation_id): Annotation removed
        mode_changed(mode): Drawing mode changed
    """

    annotation_created = Signal(object)  # ImageAnnotation
    annotation_selected = Signal(str)
    annotation_deleted = Signal(str)
    mode_changed = Signal(str)

    def __init__(
        self,
        show_toolbar: bool = True,
        default_color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._default_color = default_color or self._colors.primary
        self._current_color = self._default_color
        self._mode = AnnotationMode.SELECT
        self._annotations: Dict[str, ImageAnnotation] = {}
        self._annotation_items: Dict[str, QGraphicsItem] = {}
        self._next_id = 1

        # Drawing state
        self._drawing = False
        self._current_points: List[QPointF] = []
        self._temp_item: Optional[QGraphicsItem] = None

        self._setup_ui(show_toolbar)

    def _setup_ui(self, show_toolbar: bool):
        """Setup the widget UI"""
        self.setStyleSheet(f"""
            ImageAnnotationLayer {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        if show_toolbar:
            self._toolbar = AnnotationToolbar(colors=self._colors)
            self._toolbar.mode_changed.connect(self._on_mode_changed)
            layout.addWidget(self._toolbar)

        # Graphics view
        self._scene = QGraphicsScene()
        self._view = AnnotationView(self._scene, colors=self._colors)
        self._view.setMinimumSize(400, 300)

        # Connect view signals
        self._view.mouse_pressed.connect(self._on_mouse_press)
        self._view.mouse_moved.connect(self._on_mouse_move)
        self._view.mouse_released.connect(self._on_mouse_release)
        self._view.mouse_double_clicked.connect(self._on_mouse_double_click)

        layout.addWidget(self._view)

        # Image item
        self._image_item: Optional[QGraphicsPixmapItem] = None

    def load_image(self, path: str):
        """Load image from file path"""
        pixmap = QPixmap(path)
        self._set_pixmap(pixmap)

    def load_pixmap(self, pixmap: QPixmap):
        """Load image from QPixmap"""
        self._set_pixmap(pixmap)

    def load_qimage(self, image: QImage):
        """Load image from QImage"""
        pixmap = QPixmap.fromImage(image)
        self._set_pixmap(pixmap)

    def _set_pixmap(self, pixmap: QPixmap):
        """Set the image pixmap"""
        if self._image_item:
            self._scene.removeItem(self._image_item)

        self._image_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self._image_item)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_mode(self, mode: AnnotationMode):
        """Set the annotation mode"""
        self._mode = mode
        self._cancel_drawing()

        if hasattr(self, '_toolbar'):
            self._toolbar.set_mode(mode)

        # Update cursor
        cursors = {
            AnnotationMode.SELECT: Qt.CursorShape.ArrowCursor,
            AnnotationMode.RECTANGLE: Qt.CursorShape.CrossCursor,
            AnnotationMode.POLYGON: Qt.CursorShape.CrossCursor,
            AnnotationMode.FREEHAND: Qt.CursorShape.CrossCursor,
        }
        self._view.setCursor(cursors.get(mode, Qt.CursorShape.ArrowCursor))
        self.mode_changed.emit(mode.value)

    def _on_mode_changed(self, mode_str: str):
        """Handle toolbar mode change"""
        mode = AnnotationMode(mode_str)
        self.set_mode(mode)

    def set_annotation_color(self, color: str):
        """Set the color for new annotations"""
        self._current_color = color

    def _on_mouse_press(self, pos: QPointF):
        """Handle mouse press in scene"""
        if self._mode == AnnotationMode.SELECT:
            self._handle_select(pos)
        elif self._mode == AnnotationMode.RECTANGLE:
            self._start_rectangle(pos)
        elif self._mode == AnnotationMode.POLYGON:
            self._add_polygon_point(pos)
        elif self._mode == AnnotationMode.FREEHAND:
            self._start_freehand(pos)

    def _on_mouse_move(self, pos: QPointF):
        """Handle mouse move in scene"""
        if not self._drawing:
            return

        if self._mode == AnnotationMode.RECTANGLE:
            self._update_rectangle(pos)
        elif self._mode == AnnotationMode.FREEHAND:
            self._update_freehand(pos)

    def _on_mouse_release(self, pos: QPointF):
        """Handle mouse release in scene"""
        if self._mode == AnnotationMode.RECTANGLE and self._drawing:
            self._finish_rectangle(pos)
        elif self._mode == AnnotationMode.FREEHAND and self._drawing:
            self._finish_freehand()

    def _on_mouse_double_click(self, pos: QPointF):
        """Handle mouse double click"""
        if self._mode == AnnotationMode.POLYGON and self._drawing:
            self._finish_polygon()

    def _handle_select(self, pos: QPointF):
        """Handle selection click"""
        items = self._scene.items(pos)
        for item in items:
            for ann_id, ann_item in self._annotation_items.items():
                if item == ann_item:
                    self.annotation_selected.emit(ann_id)
                    return

    # Rectangle drawing
    def _start_rectangle(self, pos: QPointF):
        """Start drawing a rectangle"""
        self._drawing = True
        self._current_points = [pos]

        self._temp_item = QGraphicsRectItem()
        self._temp_item.setPen(self._get_pen())
        self._temp_item.setBrush(self._get_brush())
        self._scene.addItem(self._temp_item)

    def _update_rectangle(self, pos: QPointF):
        """Update rectangle while drawing"""
        if self._temp_item and self._current_points:
            start = self._current_points[0]
            rect = QRectF(start, pos).normalized()
            self._temp_item.setRect(rect)

    def _finish_rectangle(self, pos: QPointF):
        """Finish drawing rectangle"""
        if not self._current_points:
            self._cancel_drawing()
            return

        start = self._current_points[0]
        rect = QRectF(start, pos).normalized()

        # Minimum size check
        if rect.width() < 5 or rect.height() < 5:
            self._cancel_drawing()
            return

        # Create annotation
        annotation = ImageAnnotation(
            id=self._generate_id(),
            annotation_type="rectangle",
            points=[(rect.x(), rect.y(), rect.width(), rect.height())],
            color=self._current_color
        )

        self._finalize_annotation(annotation)

    # Polygon drawing
    def _add_polygon_point(self, pos: QPointF):
        """Add point to polygon"""
        if not self._drawing:
            self._drawing = True
            self._current_points = []
            self._temp_item = QGraphicsPolygonItem()
            self._temp_item.setPen(self._get_pen())
            self._temp_item.setBrush(self._get_brush())
            self._scene.addItem(self._temp_item)

        self._current_points.append(pos)
        self._update_polygon()

    def _update_polygon(self):
        """Update polygon display"""
        if self._temp_item and self._current_points:
            polygon = QPolygonF(self._current_points)
            self._temp_item.setPolygon(polygon)

    def _finish_polygon(self):
        """Finish drawing polygon"""
        if len(self._current_points) < 3:
            self._cancel_drawing()
            return

        # Create annotation
        points = [(p.x(), p.y()) for p in self._current_points]
        annotation = ImageAnnotation(
            id=self._generate_id(),
            annotation_type="polygon",
            points=points,
            color=self._current_color
        )

        self._finalize_annotation(annotation)

    # Freehand drawing
    def _start_freehand(self, pos: QPointF):
        """Start freehand drawing"""
        self._drawing = True
        self._current_points = [pos]

        self._temp_item = QGraphicsPathItem()
        self._temp_item.setPen(self._get_pen())
        self._scene.addItem(self._temp_item)

    def _update_freehand(self, pos: QPointF):
        """Update freehand path"""
        if self._temp_item and self._current_points:
            self._current_points.append(pos)

            path = QPainterPath()
            path.moveTo(self._current_points[0])
            for point in self._current_points[1:]:
                path.lineTo(point)
            self._temp_item.setPath(path)

    def _finish_freehand(self):
        """Finish freehand drawing"""
        if len(self._current_points) < 3:
            self._cancel_drawing()
            return

        # Simplify points (reduce density)
        simplified = self._simplify_points(self._current_points, tolerance=3)

        # Create annotation
        points = [(p.x(), p.y()) for p in simplified]
        annotation = ImageAnnotation(
            id=self._generate_id(),
            annotation_type="freehand",
            points=points,
            color=self._current_color
        )

        self._finalize_annotation(annotation)

    def _simplify_points(self, points: List[QPointF], tolerance: float) -> List[QPointF]:
        """Simplify point list using Douglas-Peucker algorithm"""
        if len(points) <= 2:
            return points

        # Find point with maximum distance
        max_dist = 0
        max_idx = 0
        start = points[0]
        end = points[-1]

        for i in range(1, len(points) - 1):
            dist = self._point_line_distance(points[i], start, end)
            if dist > max_dist:
                max_dist = dist
                max_idx = i

        # If max distance > tolerance, recursively simplify
        if max_dist > tolerance:
            left = self._simplify_points(points[:max_idx + 1], tolerance)
            right = self._simplify_points(points[max_idx:], tolerance)
            return left[:-1] + right
        else:
            return [start, end]

    def _point_line_distance(self, point: QPointF, line_start: QPointF, line_end: QPointF) -> float:
        """Calculate perpendicular distance from point to line"""
        dx = line_end.x() - line_start.x()
        dy = line_end.y() - line_start.y()

        if dx == 0 and dy == 0:
            return math.sqrt((point.x() - line_start.x()) ** 2 + (point.y() - line_start.y()) ** 2)

        t = ((point.x() - line_start.x()) * dx + (point.y() - line_start.y()) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))

        closest_x = line_start.x() + t * dx
        closest_y = line_start.y() + t * dy

        return math.sqrt((point.x() - closest_x) ** 2 + (point.y() - closest_y) ** 2)

    def _finalize_annotation(self, annotation: ImageAnnotation):
        """Finalize and store annotation"""
        # Remove temp item
        if self._temp_item:
            self._scene.removeItem(self._temp_item)

        # Create permanent item
        item = self._create_annotation_item(annotation)
        self._scene.addItem(item)

        # Store
        self._annotations[annotation.id] = annotation
        self._annotation_items[annotation.id] = item

        self._cancel_drawing()
        self.annotation_created.emit(annotation)

    def _create_annotation_item(self, annotation: ImageAnnotation) -> QGraphicsItem:
        """Create graphics item for annotation"""
        color = annotation.color

        if annotation.annotation_type == "rectangle":
            x, y, w, h = annotation.points[0]
            item = QGraphicsRectItem(x, y, w, h)
        elif annotation.annotation_type == "polygon":
            points = [QPointF(x, y) for x, y in annotation.points]
            item = QGraphicsPolygonItem(QPolygonF(points))
        else:  # freehand
            path = QPainterPath()
            points = annotation.points
            if points:
                path.moveTo(points[0][0], points[0][1])
                for x, y in points[1:]:
                    path.lineTo(x, y)
                path.closeSubpath()
            item = QGraphicsPathItem(path)

        item.setPen(QPen(QColor(color), 2))
        brush_color = QColor(color)
        brush_color.setAlpha(50)
        item.setBrush(QBrush(brush_color))

        return item

    def _cancel_drawing(self):
        """Cancel current drawing operation"""
        self._drawing = False
        self._current_points = []

        if self._temp_item:
            self._scene.removeItem(self._temp_item)
            self._temp_item = None

    def _get_pen(self) -> QPen:
        """Get pen for drawing"""
        return QPen(QColor(self._current_color), 2)

    def _get_brush(self) -> QBrush:
        """Get brush for drawing"""
        color = QColor(self._current_color)
        color.setAlpha(50)
        return QBrush(color)

    def _generate_id(self) -> str:
        """Generate unique annotation ID"""
        ann_id = f"ann_{self._next_id}"
        self._next_id += 1
        return ann_id

    # Public API
    def add_annotation(self, annotation: ImageAnnotation):
        """Add an existing annotation programmatically"""
        item = self._create_annotation_item(annotation)
        self._scene.addItem(item)
        self._annotations[annotation.id] = annotation
        self._annotation_items[annotation.id] = item

    def remove_annotation(self, annotation_id: str):
        """Remove an annotation by ID"""
        if annotation_id in self._annotations:
            del self._annotations[annotation_id]
        if annotation_id in self._annotation_items:
            self._scene.removeItem(self._annotation_items[annotation_id])
            del self._annotation_items[annotation_id]
        self.annotation_deleted.emit(annotation_id)

    def get_annotation(self, annotation_id: str) -> Optional[ImageAnnotation]:
        """Get annotation by ID"""
        return self._annotations.get(annotation_id)

    def get_all_annotations(self) -> List[ImageAnnotation]:
        """Get all annotations"""
        return list(self._annotations.values())

    def clear_annotations(self):
        """Remove all annotations"""
        for ann_id in list(self._annotation_items.keys()):
            self._scene.removeItem(self._annotation_items[ann_id])
        self._annotations.clear()
        self._annotation_items.clear()

    def set_annotation_color_by_id(self, annotation_id: str, color: str):
        """Update an annotation's color"""
        if annotation_id in self._annotations:
            self._annotations[annotation_id].color = color
            if annotation_id in self._annotation_items:
                item = self._annotation_items[annotation_id]
                item.setPen(QPen(QColor(color), 2))
                brush_color = QColor(color)
                brush_color.setAlpha(50)
                item.setBrush(QBrush(brush_color))

    def zoom_to_fit(self):
        """Fit view to image"""
        if self._scene.sceneRect():
            self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class AnnotationView(QGraphicsView):
    """Custom graphics view with mouse event signals"""

    mouse_pressed = Signal(QPointF)
    mouse_moved = Signal(QPointF)
    mouse_released = Signal(QPointF)
    mouse_double_clicked = Signal(QPointF)

    def __init__(self, scene: QGraphicsScene, colors: ColorPalette = None, parent=None):
        super().__init__(scene, parent)
        self._colors = colors or get_colors()

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {self._colors.surface_light};
                border: none;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self.mouse_pressed.emit(pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self.mouse_released.emit(pos)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self.mouse_double_clicked.emit(pos)
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        """Zoom with mouse wheel"""
        factor = 1.15
        if event.angleDelta().y() < 0:
            factor = 1 / factor
        self.scale(factor, factor)


class AnnotationToolbar(QFrame):
    """Toolbar for annotation tools"""

    mode_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_mode = AnnotationMode.SELECT

        self.setStyleSheet(f"""
            AnnotationToolbar {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
                padding: {SPACING.sm}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        tools = [
            (AnnotationMode.SELECT, "Select", "mdi6.cursor-default"),
            (AnnotationMode.RECTANGLE, "Rectangle", "mdi6.square-outline"),
            (AnnotationMode.POLYGON, "Polygon", "mdi6.vector-polygon"),
            (AnnotationMode.FREEHAND, "Freehand", "mdi6.draw"),
        ]

        for mode, label, icon in tools:
            btn = self._create_tool_button(label, icon, mode)
            layout.addWidget(btn)
            self._button_group.addButton(btn)

        layout.addStretch()

        self._button_group.buttonClicked.connect(self._on_button_clicked)

    def _create_tool_button(self, label: str, icon: str, mode: AnnotationMode) -> QPushButton:
        """Create a tool button"""
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setProperty("mode", mode.value)

        if mode == AnnotationMode.SELECT:
            btn.setChecked(True)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
            }}
            QPushButton:checked {{
                background-color: {self._colors.primary};
                color: white;
                border-color: {self._colors.primary};
            }}
        """)

        return btn

    def _on_button_clicked(self, button: QPushButton):
        """Handle tool button click"""
        mode = button.property("mode")
        self._current_mode = AnnotationMode(mode)
        self.mode_changed.emit(mode)

    def set_mode(self, mode: AnnotationMode):
        """Set the current mode"""
        for btn in self._button_group.buttons():
            if btn.property("mode") == mode.value:
                btn.setChecked(True)
                break
