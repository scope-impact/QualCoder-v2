"""
Network graph visualization using NetworkX + QGraphicsScene
Material Design styled interactive network graphs
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter,
    QWheelEvent, QMouseEvent
)

import networkx as nx

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


@dataclass
class GraphNode:
    """Node data for network graph"""
    id: str
    label: str
    color: Optional[str] = None
    size: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Edge data for network graph"""
    source: str
    target: str
    weight: float = 1.0
    label: str = ""
    color: Optional[str] = None


class NetworkGraphWidget(QFrame):
    """
    Interactive network graph visualization.

    Uses NetworkX for graph algorithms and layout calculation,
    QGraphicsScene for rendering and interaction.

    Usage:
        graph = NetworkGraphWidget(title="Code Co-occurrence")

        # Add nodes
        graph.add_node(GraphNode("A", "Code A", size=40))
        graph.add_node(GraphNode("B", "Code B"))
        graph.add_node(GraphNode("C", "Code C"))

        # Add edges
        graph.add_edge(GraphEdge("A", "B", weight=5))
        graph.add_edge(GraphEdge("B", "C", weight=3))

        # Apply layout and render
        graph.layout("spring")

    Signals:
        node_clicked(node_id, metadata)
        node_double_clicked(node_id, metadata)
        edge_clicked(source_id, target_id)
    """

    node_clicked = pyqtSignal(str, dict)
    node_double_clicked = pyqtSignal(str, dict)
    edge_clicked = pyqtSignal(str, str)

    def __init__(
        self,
        title: str = "",
        height: int = 400,
        interactive: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._height = height
        self._interactive = interactive

        # NetworkX graph
        self._graph = nx.Graph()
        self._node_data: Dict[str, GraphNode] = {}
        self._edge_data: Dict[Tuple[str, str], GraphEdge] = {}

        # Graphics items
        self._node_items: Dict[str, NodeItem] = {}
        self._edge_items: Dict[Tuple[str, str], EdgeItem] = {}
        self._positions: Dict[str, Tuple[float, float]] = {}

        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup the widget UI"""
        self.setStyleSheet(f"""
            NetworkGraphWidget {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Title
        if title:
            self._title_label = QLabel(title)
            self._title_label.setStyleSheet(f"""
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            layout.addWidget(self._title_label)

        # Graphics view
        self._scene = QGraphicsScene()
        self._view = GraphicsView(self._scene, interactive=self._interactive)
        self._view.setMinimumHeight(self._height)
        self._view.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {self._colors.surface_light};
                border: none;
                border-radius: {RADIUS.md}px;
            }}
        """)
        layout.addWidget(self._view)

    def add_node(self, node: GraphNode):
        """Add a node to the graph"""
        self._graph.add_node(node.id)
        self._node_data[node.id] = node

    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph"""
        self._graph.add_edge(edge.source, edge.target, weight=edge.weight)
        key = (edge.source, edge.target)
        self._edge_data[key] = edge

    def remove_node(self, node_id: str):
        """Remove a node and its edges"""
        if node_id in self._graph:
            self._graph.remove_node(node_id)
        if node_id in self._node_data:
            del self._node_data[node_id]
        if node_id in self._node_items:
            self._scene.removeItem(self._node_items[node_id])
            del self._node_items[node_id]

    def remove_edge(self, source: str, target: str):
        """Remove an edge"""
        if self._graph.has_edge(source, target):
            self._graph.remove_edge(source, target)
        key = (source, target)
        if key in self._edge_data:
            del self._edge_data[key]
        if key in self._edge_items:
            self._scene.removeItem(self._edge_items[key])
            del self._edge_items[key]

    def clear(self):
        """Clear all nodes and edges"""
        self._graph.clear()
        self._node_data.clear()
        self._edge_data.clear()
        self._node_items.clear()
        self._edge_items.clear()
        self._positions.clear()
        self._scene.clear()

    def layout(self, algorithm: str = "spring", **kwargs):
        """
        Apply layout algorithm and render the graph.

        Algorithms:
            - "spring": Force-directed layout (default)
            - "circular": Nodes arranged in circle
            - "shell": Concentric circles
            - "kamada_kawai": Energy minimization
            - "spectral": Eigenvector-based
            - "random": Random positions
        """
        if not self._graph.nodes():
            return

        # Get layout positions
        layout_funcs = {
            "spring": lambda g: nx.spring_layout(g, **kwargs),
            "circular": lambda g: nx.circular_layout(g, **kwargs),
            "shell": lambda g: nx.shell_layout(g, **kwargs),
            "kamada_kawai": lambda g: nx.kamada_kawai_layout(g, **kwargs),
            "spectral": lambda g: nx.spectral_layout(g, **kwargs),
            "random": lambda g: nx.random_layout(g, **kwargs),
        }

        layout_func = layout_funcs.get(algorithm, layout_funcs["spring"])
        positions = layout_func(self._graph)

        # Scale positions to scene
        scale = min(self._view.width(), self._view.height()) * 0.4
        center_x = self._view.width() / 2
        center_y = self._view.height() / 2

        self._positions = {}
        for node_id, (x, y) in positions.items():
            self._positions[node_id] = (
                center_x + x * scale,
                center_y + y * scale
            )

        self._render()

    def _render(self):
        """Render the graph to the scene"""
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

        if not self._positions:
            return

        # Draw edges first (behind nodes)
        for (source, target), edge in self._edge_data.items():
            if source in self._positions and target in self._positions:
                self._draw_edge(source, target, edge)

        # Draw nodes
        for node_id, node in self._node_data.items():
            if node_id in self._positions:
                self._draw_node(node_id, node)

    def _draw_node(self, node_id: str, node: GraphNode):
        """Draw a single node"""
        x, y = self._positions[node_id]
        color = node.color or self._colors.primary

        item = NodeItem(
            node_id=node_id,
            label=node.label,
            size=node.size,
            color=color,
            colors=self._colors,
            interactive=self._interactive
        )
        item.setPos(x - node.size / 2, y - node.size / 2)
        item.clicked.connect(lambda: self.node_clicked.emit(node_id, node.metadata))
        item.double_clicked.connect(lambda: self.node_double_clicked.emit(node_id, node.metadata))

        self._scene.addItem(item)
        self._node_items[node_id] = item

    def _draw_edge(self, source: str, target: str, edge: GraphEdge):
        """Draw a single edge"""
        x1, y1 = self._positions[source]
        x2, y2 = self._positions[target]
        color = edge.color or self._colors.border

        # Calculate line width based on weight
        width = max(1, min(edge.weight, 8))

        item = EdgeItem(
            x1, y1, x2, y2,
            color=color,
            width=width,
            label=edge.label,
            colors=self._colors
        )
        item.clicked.connect(lambda: self.edge_clicked.emit(source, target))

        self._scene.addItem(item)
        self._edge_items[(source, target)] = item

    def set_node_color(self, node_id: str, color: str):
        """Update a node's color"""
        if node_id in self._node_data:
            self._node_data[node_id].color = color
        if node_id in self._node_items:
            self._node_items[node_id].set_color(color)

    def set_node_size(self, node_id: str, size: int):
        """Update a node's size"""
        if node_id in self._node_data:
            self._node_data[node_id].size = size
            self._render()  # Need to re-render for size changes

    def highlight_node(self, node_id: str, highlight: bool = True):
        """Highlight or unhighlight a node"""
        if node_id in self._node_items:
            self._node_items[node_id].set_highlighted(highlight)

    def zoom_to_fit(self):
        """Zoom view to fit all content"""
        self._view.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def from_adjacency_matrix(
        self,
        matrix: List[List[float]],
        labels: List[str],
        threshold: float = 0
    ):
        """
        Create graph from adjacency matrix.

        Args:
            matrix: 2D list of edge weights
            labels: Node labels corresponding to matrix indices
            threshold: Minimum weight to create edge
        """
        self.clear()

        # Add nodes
        for i, label in enumerate(labels):
            self.add_node(GraphNode(str(i), label))

        # Add edges
        for i in range(len(matrix)):
            for j in range(i + 1, len(matrix)):
                weight = matrix[i][j]
                if weight > threshold:
                    self.add_edge(GraphEdge(str(i), str(j), weight=weight))


class GraphicsView(QGraphicsView):
    """Custom graphics view with pan and zoom"""

    def __init__(self, scene: QGraphicsScene, interactive: bool = True, parent=None):
        super().__init__(scene, parent)
        self._interactive = interactive
        self._panning = False
        self._last_pos = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event: QWheelEvent):
        """Zoom with mouse wheel"""
        if not self._interactive:
            return

        factor = 1.15
        if event.angleDelta().y() < 0:
            factor = 1 / factor
        self.scale(factor, factor)

    def mousePressEvent(self, event: QMouseEvent):
        """Start panning"""
        if event.button() == Qt.MouseButton.MiddleButton and self._interactive:
            self._panning = True
            self._last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Pan the view"""
        if self._panning and self._last_pos:
            delta = event.position() - self._last_pos
            self._last_pos = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop panning"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)


class NodeItem(QGraphicsItem):
    """Interactive node graphics item"""

    clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(
        self,
        node_id: str,
        label: str,
        size: int = 30,
        color: str = "#009688",
        colors: ColorPalette = None,
        interactive: bool = True,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._node_id = node_id
        self._label = label
        self._size = size
        self._color = color
        self._interactive = interactive
        self._highlighted = False
        self._hovered = False

        # Signals (using custom implementation since QGraphicsItem doesn't have signals)
        self.clicked = SignalEmitter()
        self.double_clicked = SignalEmitter()

        if interactive:
            self.setAcceptHoverEvents(True)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw shadow when highlighted
        if self._highlighted:
            shadow_color = QColor(self._color)
            shadow_color.setAlpha(100)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(-2, -2, self._size + 4, self._size + 4))

        # Draw node circle
        color = QColor(self._color)
        if self._hovered:
            color = color.lighter(120)

        painter.setBrush(QBrush(color))
        pen = QPen(QColor(self._colors.surface), 2)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(0, 0, self._size, self._size))

        # Draw label
        painter.setPen(QPen(QColor(self._colors.text_primary)))
        font = QFont("Roboto", 9)
        painter.setFont(font)

        # Center label below node
        text_rect = painter.fontMetrics().boundingRect(self._label)
        x = (self._size - text_rect.width()) / 2
        y = self._size + 15
        painter.drawText(int(x), int(y), self._label)

    def set_color(self, color: str):
        """Update node color"""
        self._color = color
        self.update()

    def set_highlighted(self, highlighted: bool):
        """Set highlight state"""
        self._highlighted = highlighted
        self.update()

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class EdgeItem(QGraphicsLineItem):
    """Interactive edge graphics item"""

    def __init__(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        color: str = "#E0E0E0",
        width: float = 1,
        label: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(x1, y1, x2, y2, parent)
        self._colors = colors or get_theme("light")
        self._label = label

        # Signals
        self.clicked = SignalEmitter()

        pen = QPen(QColor(color), width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)

        # Draw label at midpoint
        if self._label:
            line = self.line()
            mid_x = (line.x1() + line.x2()) / 2
            mid_y = (line.y1() + line.y2()) / 2

            painter.setPen(QPen(QColor(self._colors.text_secondary)))
            font = QFont("Roboto", 8)
            painter.setFont(font)
            painter.drawText(int(mid_x), int(mid_y), self._label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SignalEmitter:
    """Simple signal emitter for QGraphicsItem (which doesn't support pyqtSignal)"""

    def __init__(self):
        self._callbacks = []

    def connect(self, callback: Callable):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)
