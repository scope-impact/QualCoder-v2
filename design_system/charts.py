"""
Chart components using PyQtGraph
Material Design styled charts with theme support
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors

# Configure pyqtgraph defaults
pg.setConfigOptions(antialias=True, background=None)


@dataclass
class ChartDataPoint:
    """Single data point for charts"""

    label: str
    value: float
    color: str | None = None


class ChartWidget(QFrame):
    """
    Base chart widget with PyQtGraph integration.

    Wraps PyQtGraph's PlotWidget with design system theming
    and common configuration.

    Usage:
        chart = ChartWidget(title="Code Frequency")
        chart.set_bar_data([
            ChartDataPoint("Code A", 45),
            ChartDataPoint("Code B", 32),
            ChartDataPoint("Code C", 28),
        ])
    """

    point_clicked = Signal(int, object)  # index, data

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        show_legend: bool = True,
        height: int = 300,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._title = title
        self._subtitle = subtitle
        self._show_legend = show_legend
        self._data = []

        self.setStyleSheet(f"""
            ChartWidget {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Header
        if title or subtitle:
            header = QVBoxLayout()
            header.setSpacing(SPACING.xs)

            if title:
                self._title_label = QLabel(title)
                self._title_label.setStyleSheet(f"""
                    color: {self._colors.text_primary};
                    font-size: {TYPOGRAPHY.text_lg}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                """)
                header.addWidget(self._title_label)

            if subtitle:
                self._subtitle_label = QLabel(subtitle)
                self._subtitle_label.setStyleSheet(f"""
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                """)
                header.addWidget(self._subtitle_label)

            layout.addLayout(header)

        # Plot widget
        self._plot = pg.PlotWidget()
        self._plot.setMinimumHeight(height)
        self._configure_plot()
        layout.addWidget(self._plot)

        # Legend container
        if show_legend:
            self._legend_container = QHBoxLayout()
            self._legend_container.setSpacing(SPACING.lg)
            layout.addLayout(self._legend_container)

    def _configure_plot(self):
        """Configure plot appearance for design system"""
        plot = self._plot

        # Background
        plot.setBackground(self._colors.surface)

        # Axes
        axis_pen = pg.mkPen(color=self._colors.border, width=1)
        text_color = self._colors.text_secondary

        for axis in ["left", "bottom"]:
            ax = plot.getAxis(axis)
            ax.setPen(axis_pen)
            ax.setTextPen(pg.mkPen(color=text_color))
            ax.setStyle(tickFont=pg.QtGui.QFont("Roboto", 10))

        # Grid
        plot.showGrid(x=True, y=True, alpha=0.1)

        # Remove top/right axes
        plot.hideAxis("top")
        plot.hideAxis("right")

    def _get_chart_colors(self, count: int) -> list[str]:
        """Get color palette for chart series"""
        palette = [
            self._colors.primary,
            self._colors.secondary,
            self._colors.success,
            self._colors.warning,
            self._colors.info,
            self._colors.code_purple,
            self._colors.code_cyan,
            self._colors.code_pink,
        ]
        # Cycle through palette if needed
        return [palette[i % len(palette)] for i in range(count)]

    def set_bar_data(
        self,
        data: list[ChartDataPoint],
        horizontal: bool = False,
        bar_width: float = 0.6,
    ):
        """
        Set bar chart data.

        Args:
            data: List of ChartDataPoint with label, value, optional color
            horizontal: If True, draw horizontal bars
            bar_width: Width of bars (0-1)
        """
        self._data = data
        self._plot.clear()

        colors = self._get_chart_colors(len(data))
        x = np.arange(len(data))
        values = [d.value for d in data]
        labels = [d.label for d in data]

        # Create bar graph
        bar_colors = [QColor(d.color or colors[i]) for i, d in enumerate(data)]
        brushes = [pg.mkBrush(c) for c in bar_colors]

        if horizontal:
            bar = pg.BarGraphItem(
                x0=0, y=x, height=bar_width, width=values, brushes=brushes
            )
            self._plot.getAxis("left").setTicks(
                [[(i, labels[i]) for i in range(len(labels))]]
            )
        else:
            bar = pg.BarGraphItem(x=x, height=values, width=bar_width, brushes=brushes)
            self._plot.getAxis("bottom").setTicks(
                [[(i, labels[i]) for i in range(len(labels))]]
            )

        self._plot.addItem(bar)
        self._update_legend(data, colors)

    def set_line_data(self, series: list[dict[str, Any]], show_points: bool = True):
        """
        Set line chart data.

        Args:
            series: List of {name, values, color?} dicts
            show_points: Show data points on lines

        Example:
            chart.set_line_data([
                {"name": "2024", "values": [10, 20, 30, 25, 40]},
                {"name": "2025", "values": [15, 25, 35, 30, 45]},
            ])
        """
        self._plot.clear()
        colors = self._get_chart_colors(len(series))

        legend_data = []
        for i, s in enumerate(series):
            color = s.get("color", colors[i])
            pen = pg.mkPen(color=color, width=2)
            y = s["values"]
            x = np.arange(len(y))

            self._plot.plot(x, y, pen=pen, name=s.get("name", f"Series {i + 1}"))

            if show_points:
                scatter = pg.ScatterPlotItem(
                    x=x,
                    y=y,
                    size=8,
                    brush=pg.mkBrush(color),
                    pen=pg.mkPen(self._colors.surface, width=2),
                )
                self._plot.addItem(scatter)

            legend_data.append(
                ChartDataPoint(s.get("name", f"Series {i + 1}"), 0, color)
            )

        self._update_legend(legend_data, colors)

    def set_scatter_data(
        self,
        points: list[tuple[float, float]],
        labels: list[str] = None,
        color: str = None,
    ):
        """
        Set scatter plot data.

        Args:
            points: List of (x, y) tuples
            labels: Optional labels for each point
            color: Optional single color for all points
        """
        self._scatter_labels = labels  # Store for tooltip display
        self._plot.clear()

        x = [p[0] for p in points]
        y = [p[1] for p in points]

        scatter = pg.ScatterPlotItem(
            x=x,
            y=y,
            size=10,
            brush=pg.mkBrush(color or self._colors.primary),
            pen=pg.mkPen(self._colors.surface, width=2),
        )
        self._plot.addItem(scatter)

    def _update_legend(self, data: list[ChartDataPoint], colors: list[str]):
        """Update legend items"""
        if not self._show_legend:
            return

        # Clear existing legend
        while self._legend_container.count():
            item = self._legend_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, d in enumerate(data):
            color = d.color or colors[i]
            item = LegendItem(d.label, color, colors=self._colors)
            self._legend_container.addWidget(item)

        self._legend_container.addStretch()

    def set_title(self, title: str):
        """Update chart title"""
        if hasattr(self, "_title_label"):
            self._title_label.setText(title)

    def clear(self):
        """Clear all chart data"""
        self._plot.clear()
        self._data = []


class PieChart(QFrame):
    """
    Pie chart component with design system theming.

    Native Qt implementation since PyQtGraph doesn't have pie charts.

    Usage:
        pie = PieChart(title="Distribution")
        pie.set_data([
            ChartDataPoint("Category A", 45),
            ChartDataPoint("Category B", 30),
            ChartDataPoint("Category C", 25),
        ])
    """

    slice_clicked = Signal(int, object)  # index, data

    def __init__(
        self,
        title: str = "",
        show_legend: bool = True,
        show_labels: bool = True,
        donut: bool = False,
        size: int = 200,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._data: list[ChartDataPoint] = []
        self._show_labels = show_labels
        self._donut = donut
        self._size = size

        self.setStyleSheet(f"""
            PieChart {{
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

        # Pie canvas
        self._canvas = PieCanvas(
            size=size, donut=donut, show_labels=show_labels, colors=self._colors
        )
        layout.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Legend
        if show_legend:
            self._legend_container = QHBoxLayout()
            self._legend_container.setSpacing(SPACING.lg)
            layout.addLayout(self._legend_container)

    def set_data(self, data: list[ChartDataPoint]):
        """Set pie chart data"""
        self._data = data

        # Assign colors if not provided
        palette = self._get_chart_colors(len(data))
        for i, d in enumerate(data):
            if not d.color:
                d.color = palette[i]

        self._canvas.set_data(data)
        self._update_legend(data)

    def _get_chart_colors(self, count: int) -> list[str]:
        """Get color palette for chart slices"""
        palette = [
            self._colors.primary,
            self._colors.secondary,
            self._colors.success,
            self._colors.warning,
            self._colors.info,
            self._colors.code_purple,
            self._colors.code_cyan,
            self._colors.code_pink,
        ]
        return [palette[i % len(palette)] for i in range(count)]

    def _update_legend(self, data: list[ChartDataPoint]):
        """Update legend items"""
        if not hasattr(self, "_legend_container"):
            return

        # Clear existing legend
        while self._legend_container.count():
            item = self._legend_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for d in data:
            item = LegendItem(d.label, d.color, colors=self._colors)
            self._legend_container.addWidget(item)

        self._legend_container.addStretch()


class PieCanvas(QWidget):
    """Custom pie chart drawing widget"""

    def __init__(
        self,
        size: int = 200,
        donut: bool = False,
        show_labels: bool = True,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._data: list[ChartDataPoint] = []
        self._donut = donut
        self._show_labels = show_labels

        self.setFixedSize(size, size)

    def set_data(self, data: list[ChartDataPoint]):
        """Set pie data and redraw"""
        self._data = data
        self.update()

    def paintEvent(self, _event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate total
        total = sum(d.value for d in self._data)
        if total == 0:
            return

        # Pie geometry
        margin = 10
        size = min(self.width(), self.height()) - 2 * margin
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Draw slices
        start_angle = 90 * 16  # Start at top (Qt uses 1/16 degrees)

        for d in self._data:
            span_angle = int(-(d.value / total) * 360 * 16)  # Negative for clockwise

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(d.color)))
            painter.drawPie(rect, start_angle, span_angle)

            start_angle += span_angle

        # Draw donut hole
        if self._donut:
            hole_size = size * 0.5
            hole_margin = (self.width() - hole_size) / 2
            hole_rect = self.rect().adjusted(
                int(hole_margin), int(hole_margin), int(-hole_margin), int(-hole_margin)
            )
            painter.setBrush(QBrush(QColor(self._colors.surface)))
            painter.drawEllipse(hole_rect)


class LegendItem(QFrame):
    """Legend item with color indicator and label"""

    def __init__(
        self, label: str, color: str, colors: ColorPalette = None, parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # Color indicator
        indicator = QFrame()
        indicator.setFixedSize(12, 12)
        indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 2px;
        """)
        layout.addWidget(indicator)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(label_widget)


class SparkLine(QWidget):
    """
    Compact sparkline chart for inline data visualization.

    Usage:
        spark = SparkLine(values=[10, 25, 15, 30, 20, 35])
    """

    def __init__(
        self,
        values: list[float] = None,
        width: int = 80,
        height: int = 24,
        color: str = None,
        show_endpoint: bool = True,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._values = values or []
        self._color = color or self._colors.primary
        self._show_endpoint = show_endpoint

        self.setFixedSize(width, height)

    def set_values(self, values: list[float]):
        """Update sparkline values"""
        self._values = values
        self.update()

    def paintEvent(self, _event):
        if len(self._values) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Normalize values
        min_val = min(self._values)
        max_val = max(self._values)
        range_val = max_val - min_val if max_val != min_val else 1

        margin = 4
        w = self.width() - 2 * margin
        h = self.height() - 2 * margin

        # Calculate points
        points = []
        for i, v in enumerate(self._values):
            x = margin + (i / (len(self._values) - 1)) * w
            y = margin + h - ((v - min_val) / range_val) * h
            points.append((x, y))

        # Draw line
        pen = QPen(QColor(self._color), 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)
        painter.drawPath(path)

        # Draw endpoint
        if self._show_endpoint and points:
            last_x, last_y = points[-1]
            painter.setBrush(QBrush(QColor(self._color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(last_x - 3), int(last_y - 3), 6, 6)
