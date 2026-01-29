"""
Tests for visualization components:
ChartWidget, PieChart, NetworkGraphWidget, WordCloudWidget,
ImageAnnotationLayer, HeatMapCell, RelevanceScoreBar
"""

import pytest
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPixmap, QImage, QColor

from design_system.charts import (
    ChartWidget, PieChart, ChartDataPoint, SparkLine, LegendItem
)
from design_system.network_graph import (
    NetworkGraphWidget, GraphNode, GraphEdge
)
from design_system.word_cloud import WordCloudWidget, WordCloudPreview
from design_system.image_annotation import (
    ImageAnnotationLayer, ImageAnnotation, AnnotationMode
)
from design_system.data_display import HeatMapCell, HeatMapGrid
from design_system.progress_bar import (
    RelevanceScoreBar, RelevanceBarWidget, ScoreIndicator
)


class TestChartWidget:
    """Tests for ChartWidget component"""

    def test_chart_creation(self, qtbot):
        """ChartWidget should be created with title"""
        chart = ChartWidget(title="Test Chart")
        qtbot.addWidget(chart)

        assert chart is not None
        assert chart._title == "Test Chart"

    def test_chart_bar_data(self, qtbot):
        """ChartWidget should accept bar chart data"""
        chart = ChartWidget(title="Bar Chart")
        qtbot.addWidget(chart)

        data = [
            ChartDataPoint("A", 10),
            ChartDataPoint("B", 20),
            ChartDataPoint("C", 15),
        ]
        chart.set_bar_data(data)

        assert len(chart._data) == 3

    def test_chart_line_data(self, qtbot):
        """ChartWidget should accept line chart data"""
        chart = ChartWidget(title="Line Chart")
        qtbot.addWidget(chart)

        series = [
            {"name": "Series 1", "values": [10, 20, 30]},
            {"name": "Series 2", "values": [15, 25, 35]},
        ]
        chart.set_line_data(series)

        # Should not raise
        assert chart is not None

    def test_chart_scatter_data(self, qtbot):
        """ChartWidget should accept scatter plot data"""
        chart = ChartWidget(title="Scatter")
        qtbot.addWidget(chart)

        points = [(1, 2), (3, 4), (5, 6)]
        chart.set_scatter_data(points)

        assert chart is not None

    def test_chart_clear(self, qtbot):
        """ChartWidget should clear data"""
        chart = ChartWidget()
        qtbot.addWidget(chart)

        chart.set_bar_data([ChartDataPoint("A", 10)])
        chart.clear()

        assert len(chart._data) == 0

    def test_chart_color_palette(self, qtbot):
        """ChartWidget should provide colors for data"""
        chart = ChartWidget()
        qtbot.addWidget(chart)

        colors = chart._get_chart_colors(5)
        assert len(colors) == 5


class TestPieChart:
    """Tests for PieChart component"""

    def test_pie_chart_creation(self, qtbot):
        """PieChart should be created"""
        pie = PieChart(title="Distribution")
        qtbot.addWidget(pie)

        assert pie is not None

    def test_pie_chart_data(self, qtbot):
        """PieChart should accept data"""
        pie = PieChart(title="Test")
        qtbot.addWidget(pie)

        data = [
            ChartDataPoint("A", 50),
            ChartDataPoint("B", 30),
            ChartDataPoint("C", 20),
        ]
        pie.set_data(data)

        assert len(pie._data) == 3

    def test_pie_chart_donut(self, qtbot):
        """PieChart should support donut style"""
        pie = PieChart(donut=True)
        qtbot.addWidget(pie)

        assert pie._canvas._donut is True


class TestSparkLine:
    """Tests for SparkLine component"""

    def test_sparkline_creation(self, qtbot):
        """SparkLine should be created"""
        spark = SparkLine(values=[10, 20, 15, 25, 30])
        qtbot.addWidget(spark)

        assert spark is not None
        assert len(spark._values) == 5

    def test_sparkline_update(self, qtbot):
        """SparkLine should update values"""
        spark = SparkLine()
        qtbot.addWidget(spark)

        spark.set_values([5, 10, 15])
        assert len(spark._values) == 3


class TestNetworkGraphWidget:
    """Tests for NetworkGraphWidget component"""

    def test_graph_creation(self, qtbot):
        """NetworkGraphWidget should be created"""
        graph = NetworkGraphWidget(title="Test Graph")
        qtbot.addWidget(graph)

        assert graph is not None

    def test_graph_add_nodes(self, qtbot):
        """NetworkGraphWidget should add nodes"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        graph.add_node(GraphNode("A", "Node A"))
        graph.add_node(GraphNode("B", "Node B"))

        assert len(graph._node_data) == 2

    def test_graph_add_edges(self, qtbot):
        """NetworkGraphWidget should add edges"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        graph.add_node(GraphNode("A", "Node A"))
        graph.add_node(GraphNode("B", "Node B"))
        graph.add_edge(GraphEdge("A", "B", weight=5))

        assert len(graph._edge_data) == 1

    def test_graph_layout(self, qtbot):
        """NetworkGraphWidget should apply layout"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        graph.add_node(GraphNode("A", "Node A"))
        graph.add_node(GraphNode("B", "Node B"))
        graph.add_edge(GraphEdge("A", "B"))
        graph.layout("spring")

        assert len(graph._positions) == 2

    def test_graph_clear(self, qtbot):
        """NetworkGraphWidget should clear all data"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        graph.add_node(GraphNode("A", "Node A"))
        graph.clear()

        assert len(graph._node_data) == 0

    def test_graph_remove_node(self, qtbot):
        """NetworkGraphWidget should remove nodes"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        graph.add_node(GraphNode("A", "Node A"))
        graph.add_node(GraphNode("B", "Node B"))
        graph.remove_node("A")

        assert "A" not in graph._node_data
        assert "B" in graph._node_data

    def test_graph_from_matrix(self, qtbot):
        """NetworkGraphWidget should create from adjacency matrix"""
        graph = NetworkGraphWidget()
        qtbot.addWidget(graph)

        matrix = [
            [0, 5, 0],
            [5, 0, 3],
            [0, 3, 0],
        ]
        labels = ["A", "B", "C"]
        graph.from_adjacency_matrix(matrix, labels, threshold=0)

        assert len(graph._node_data) == 3


class TestWordCloudWidget:
    """Tests for WordCloudWidget component"""

    def test_wordcloud_creation(self, qtbot):
        """WordCloudWidget should be created"""
        wc = WordCloudWidget(title="Word Cloud")
        qtbot.addWidget(wc)

        assert wc is not None

    def test_wordcloud_frequencies(self, qtbot):
        """WordCloudWidget should accept frequencies"""
        wc = WordCloudWidget()
        qtbot.addWidget(wc)

        wc.set_frequencies({
            "test": 10,
            "word": 8,
            "cloud": 5,
        })

        assert len(wc._frequencies) == 3
        assert wc._wordcloud is not None

    def test_wordcloud_color_scheme(self, qtbot):
        """WordCloudWidget should change color scheme"""
        wc = WordCloudWidget()
        qtbot.addWidget(wc)

        wc.set_color_scheme("rainbow")
        assert wc._color_scheme == "rainbow"

    def test_wordcloud_clear(self, qtbot):
        """WordCloudWidget should clear"""
        wc = WordCloudWidget()
        qtbot.addWidget(wc)

        wc.set_frequencies({"test": 10})
        wc.clear()

        assert len(wc._frequencies) == 0


class TestWordCloudPreview:
    """Tests for WordCloudPreview component"""

    def test_preview_creation(self, qtbot):
        """WordCloudPreview should be created"""
        preview = WordCloudPreview()
        qtbot.addWidget(preview)

        assert preview is not None

    def test_preview_frequencies(self, qtbot):
        """WordCloudPreview should display frequencies"""
        preview = WordCloudPreview()
        qtbot.addWidget(preview)

        preview.set_frequencies({"test": 10, "word": 5})
        # Should not raise
        assert preview is not None


class TestImageAnnotationLayer:
    """Tests for ImageAnnotationLayer component"""

    def test_annotation_layer_creation(self, qtbot):
        """ImageAnnotationLayer should be created"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        assert layer is not None

    def test_annotation_load_pixmap(self, qtbot):
        """ImageAnnotationLayer should load pixmap"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        # Create a test pixmap
        pixmap = QPixmap(100, 100)
        pixmap.fill(QColor("white"))
        layer.load_pixmap(pixmap)

        assert layer._image_item is not None

    def test_annotation_set_mode(self, qtbot):
        """ImageAnnotationLayer should change mode"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        layer.set_mode(AnnotationMode.RECTANGLE)
        assert layer._mode == AnnotationMode.RECTANGLE

        layer.set_mode(AnnotationMode.POLYGON)
        assert layer._mode == AnnotationMode.POLYGON

    def test_annotation_add_programmatically(self, qtbot):
        """ImageAnnotationLayer should add annotations programmatically"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        annotation = ImageAnnotation(
            id="test_1",
            annotation_type="rectangle",
            points=[(10, 10, 50, 50)],
            color="#FF0000"
        )
        layer.add_annotation(annotation)

        assert len(layer._annotations) == 1
        assert "test_1" in layer._annotations

    def test_annotation_remove(self, qtbot):
        """ImageAnnotationLayer should remove annotations"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        annotation = ImageAnnotation(
            id="test_1",
            annotation_type="rectangle",
            points=[(10, 10, 50, 50)]
        )
        layer.add_annotation(annotation)
        layer.remove_annotation("test_1")

        assert len(layer._annotations) == 0

    def test_annotation_clear(self, qtbot):
        """ImageAnnotationLayer should clear all annotations"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        layer.add_annotation(ImageAnnotation("a", "rectangle", [(0, 0, 10, 10)]))
        layer.add_annotation(ImageAnnotation("b", "rectangle", [(20, 20, 10, 10)]))
        layer.clear_annotations()

        assert len(layer._annotations) == 0

    def test_annotation_get_all(self, qtbot):
        """ImageAnnotationLayer should return all annotations"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        layer.add_annotation(ImageAnnotation("a", "rectangle", [(0, 0, 10, 10)]))
        layer.add_annotation(ImageAnnotation("b", "polygon", [(0, 0), (10, 0), (10, 10)]))

        annotations = layer.get_all_annotations()
        assert len(annotations) == 2

    def test_annotation_color_change(self, qtbot):
        """ImageAnnotationLayer should change annotation color"""
        layer = ImageAnnotationLayer()
        qtbot.addWidget(layer)

        annotation = ImageAnnotation("test", "rectangle", [(0, 0, 10, 10)], color="#FF0000")
        layer.add_annotation(annotation)
        layer.set_annotation_color_by_id("test", "#00FF00")

        assert layer._annotations["test"].color == "#00FF00"


class TestHeatMapCell:
    """Tests for HeatMapCell component"""

    def test_heatmap_cell_creation(self, qtbot):
        """HeatMapCell should be created"""
        cell = HeatMapCell(value=0.5)
        qtbot.addWidget(cell)

        assert cell is not None
        assert cell._value == 0.5

    def test_heatmap_cell_value_update(self, qtbot):
        """HeatMapCell should update value"""
        cell = HeatMapCell(value=0)
        qtbot.addWidget(cell)

        cell.set_value(0.75)
        assert cell.value() == 0.75

    def test_heatmap_cell_color_schemes(self, qtbot):
        """HeatMapCell should support different color schemes"""
        schemes = ["primary", "sequential", "diverging", "success"]

        for scheme in schemes:
            cell = HeatMapCell(value=0.5, color_scheme=scheme)
            qtbot.addWidget(cell)
            assert cell is not None

    def test_heatmap_cell_range(self, qtbot):
        """HeatMapCell should support custom range"""
        cell = HeatMapCell(value=50, min_value=0, max_value=100)
        qtbot.addWidget(cell)

        # Should normalize to 0.5
        assert cell._normalize_value() == 0.5


class TestHeatMapGrid:
    """Tests for HeatMapGrid component"""

    def test_heatmap_grid_creation(self, qtbot):
        """HeatMapGrid should be created"""
        grid = HeatMapGrid(
            row_labels=["A", "B"],
            col_labels=["X", "Y"],
            values=[[0.5, 0.8], [0.3, 1.0]]
        )
        qtbot.addWidget(grid)

        assert grid is not None
        assert len(grid._cells) == 2

    def test_heatmap_grid_set_value(self, qtbot):
        """HeatMapGrid should update individual cells"""
        grid = HeatMapGrid(
            row_labels=["A"],
            col_labels=["X"],
            values=[[0.5]]
        )
        qtbot.addWidget(grid)

        grid.set_value(0, 0, 0.9)
        assert grid.get_value(0, 0) == 0.9


class TestRelevanceScoreBar:
    """Tests for RelevanceScoreBar component"""

    def test_score_bar_creation(self, qtbot):
        """RelevanceScoreBar should be created"""
        bar = RelevanceScoreBar(score=0.85, label="Relevance")
        qtbot.addWidget(bar)

        assert bar is not None
        assert bar._score == 0.85

    def test_score_bar_update(self, qtbot):
        """RelevanceScoreBar should update score"""
        bar = RelevanceScoreBar(score=0.5)
        qtbot.addWidget(bar)

        bar.set_score(0.9)
        assert bar.score() == 0.9

    def test_score_bar_clamp(self, qtbot):
        """RelevanceScoreBar should clamp score to 0-1"""
        bar = RelevanceScoreBar()
        qtbot.addWidget(bar)

        bar.set_score(1.5)
        assert bar.score() == 1.0

        bar.set_score(-0.5)
        assert bar.score() == 0.0

    def test_score_bar_variants(self, qtbot):
        """RelevanceScoreBar should support variants"""
        variants = ["default", "confidence", "match", "gradient"]

        for variant in variants:
            bar = RelevanceScoreBar(score=0.7, variant=variant)
            qtbot.addWidget(bar)
            assert bar is not None


class TestScoreIndicator:
    """Tests for ScoreIndicator component"""

    def test_score_indicator_creation(self, qtbot):
        """ScoreIndicator should be created"""
        indicator = ScoreIndicator(label="Confidence", score=0.75)
        qtbot.addWidget(indicator)

        assert indicator is not None

    def test_score_indicator_update(self, qtbot):
        """ScoreIndicator should update score"""
        indicator = ScoreIndicator(score=0.5)
        qtbot.addWidget(indicator)

        indicator.set_score(0.8)
        # Check percentage label updated
        assert indicator._percentage.text() == "80%"


class TestLegendItem:
    """Tests for LegendItem component"""

    def test_legend_item_creation(self, qtbot):
        """LegendItem should be created"""
        item = LegendItem(label="Series A", color="#FF0000")
        qtbot.addWidget(item)

        assert item is not None


# PDF Viewer tests
from design_system.pdf_viewer import (
    PDFPageViewer, PDFGraphicsView, PDFThumbnail,
    PDFTextBlock, PDFSelection, HAS_PYMUPDF
)


class TestPDFPageViewer:
    """Tests for PDFPageViewer component"""

    def test_viewer_creation(self, qtbot):
        """PDFPageViewer should be created"""
        viewer = PDFPageViewer()
        qtbot.addWidget(viewer)

        assert viewer is not None

    def test_viewer_with_toolbar(self, qtbot):
        """PDFPageViewer should create with toolbar"""
        viewer = PDFPageViewer(show_toolbar=True)
        qtbot.addWidget(viewer)

        assert hasattr(viewer, '_toolbar')

    def test_viewer_with_thumbnails(self, qtbot):
        """PDFPageViewer should create with thumbnail panel"""
        viewer = PDFPageViewer(show_thumbnails=True)
        qtbot.addWidget(viewer)

        assert hasattr(viewer, '_thumbnail_panel')

    def test_viewer_initial_state(self, qtbot):
        """PDFPageViewer should have correct initial state"""
        viewer = PDFPageViewer(initial_zoom=1.5)
        qtbot.addWidget(viewer)

        assert viewer._zoom == 1.5
        assert viewer._current_page == 0
        assert viewer._page_count == 0

    def test_viewer_zoom(self, qtbot):
        """PDFPageViewer should change zoom level"""
        viewer = PDFPageViewer()
        qtbot.addWidget(viewer)

        viewer.set_zoom(2.0)
        assert viewer._zoom == 2.0

        viewer.zoom_in()
        assert viewer._zoom == 2.25

        viewer.zoom_out()
        assert viewer._zoom == 2.0

    def test_viewer_zoom_limits(self, qtbot):
        """PDFPageViewer should respect zoom limits"""
        viewer = PDFPageViewer()
        qtbot.addWidget(viewer)

        viewer.set_zoom(10.0)  # Above max
        assert viewer._zoom == 4.0

        viewer.set_zoom(0.1)  # Below min
        assert viewer._zoom == 0.25

    def test_viewer_properties(self, qtbot):
        """PDFPageViewer should expose properties"""
        viewer = PDFPageViewer()
        qtbot.addWidget(viewer)

        assert viewer.current_page == 0
        assert viewer.page_count == 0
        assert viewer.zoom == 1.0


class TestPDFGraphicsView:
    """Tests for PDFGraphicsView component"""

    def test_view_creation(self, qtbot):
        """PDFGraphicsView should be created"""
        view = PDFGraphicsView()
        qtbot.addWidget(view)

        assert view is not None
        assert view.scene() is not None

    def test_view_set_page(self, qtbot):
        """PDFGraphicsView should display page pixmap"""
        view = PDFGraphicsView()
        qtbot.addWidget(view)

        pixmap = QPixmap(200, 300)
        pixmap.fill(QColor("white"))
        view.set_page(pixmap)

        # Scene should contain items
        assert len(view.scene().items()) > 0

    def test_view_clear_selection(self, qtbot):
        """PDFGraphicsView should clear selection"""
        view = PDFGraphicsView()
        qtbot.addWidget(view)

        view.clear_selection()
        assert view._selection_rect is None


class TestPDFThumbnail:
    """Tests for PDFThumbnail component"""

    def test_thumbnail_creation(self, qtbot):
        """PDFThumbnail should be created"""
        pixmap = QPixmap(80, 100)
        pixmap.fill(QColor("white"))

        thumb = PDFThumbnail(pixmap, page_number=1)
        qtbot.addWidget(thumb)

        assert thumb is not None
        assert thumb._page_number == 1

    def test_thumbnail_selection(self, qtbot):
        """PDFThumbnail should track selection state"""
        pixmap = QPixmap(80, 100)
        pixmap.fill(QColor("white"))

        thumb = PDFThumbnail(pixmap, page_number=1, selected=False)
        qtbot.addWidget(thumb)

        assert thumb._selected is False

        thumb.set_selected(True)
        assert thumb._selected is True


class TestPDFDataClasses:
    """Tests for PDF data classes"""

    def test_pdf_text_block(self):
        """PDFTextBlock should hold text data"""
        block = PDFTextBlock(
            text="Sample text",
            rect=(10, 20, 100, 50),
            page=0
        )

        assert block.text == "Sample text"
        assert block.rect == (10, 20, 100, 50)
        assert block.page == 0

    def test_pdf_selection(self):
        """PDFSelection should hold selection data"""
        selection = PDFSelection(
            page=5,
            rect=(0, 0, 100, 50),
            text="Selected text"
        )

        assert selection.page == 5
        assert selection.text == "Selected text"

    def test_pdf_selection_defaults(self):
        """PDFSelection should have default text"""
        selection = PDFSelection(page=0, rect=(0, 0, 10, 10))

        assert selection.text == ""
