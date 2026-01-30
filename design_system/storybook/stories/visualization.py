"""
Visualization component stories: charts, graphs, word clouds, annotations
"""

from typing import List, Tuple

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPixmap, QColor

from ...tokens import SPACING, ColorPalette
from ...charts import ChartWidget, PieChart, ChartDataPoint, SparkLine
from ...network_graph import NetworkGraphWidget, GraphNode, GraphEdge
from ...word_cloud import WordCloudWidget
from ...image_annotation import ImageAnnotationLayer, AnnotationMode
from ...data_display import HeatMapCell, HeatMapGrid
from ...progress_bar import RelevanceScoreBar, ScoreIndicator
from ...pdf_viewer import PDFPageViewer
from ..page import StoryPage


def create_charts_story(colors: ColorPalette) -> StoryPage:
    """Charts story with bar, line, pie examples"""
    examples = []

    # Bar chart
    bar_chart = ChartWidget(title="Code Frequency", height=200, colors=colors)
    bar_chart.set_bar_data([
        ChartDataPoint("Learning", 45),
        ChartDataPoint("Experience", 38),
        ChartDataPoint("Emotions", 32),
        ChartDataPoint("Goals", 28),
        ChartDataPoint("Challenges", 22),
    ])
    examples.append((
        "Bar Chart",
        bar_chart,
        'chart = ChartWidget(title="Code Frequency")\n'
        'chart.set_bar_data([ChartDataPoint("Code", 45), ...])'
    ))

    # Line chart
    line_chart = ChartWidget(title="Coding Over Time", height=200, colors=colors)
    line_chart.set_line_data([
        {"name": "Week 1", "values": [10, 15, 12, 18, 22, 20, 25]},
        {"name": "Week 2", "values": [12, 18, 20, 25, 30, 28, 35]},
    ])
    examples.append((
        "Line Chart",
        line_chart,
        'chart = ChartWidget(title="Trend")\n'
        'chart.set_line_data([{"name": "Series", "values": [...]}])'
    ))

    # Pie chart
    pie_chart = PieChart(title="Distribution", size=180, colors=colors)
    pie_chart.set_data([
        ChartDataPoint("Text Files", 45),
        ChartDataPoint("Audio", 30),
        ChartDataPoint("Video", 15),
        ChartDataPoint("Images", 10),
    ])
    examples.append((
        "Pie Chart",
        pie_chart,
        'pie = PieChart(title="Distribution")\n'
        'pie.set_data([ChartDataPoint("Category", 45), ...])'
    ))

    # Donut chart
    donut_chart = PieChart(title="Code Coverage", size=180, donut=True, colors=colors)
    donut_chart.set_data([
        ChartDataPoint("Coded", 75),
        ChartDataPoint("Uncoded", 25),
    ])
    examples.append((
        "Donut Chart",
        donut_chart,
        'PieChart(title="Coverage", donut=True)'
    ))

    # Sparklines
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.xl)

    spark1 = SparkLine(values=[10, 15, 12, 18, 22, 20, 25, 30], colors=colors)
    spark2 = SparkLine(values=[30, 28, 25, 22, 20, 18, 15, 12], color=colors.error, colors=colors)
    spark3 = SparkLine(values=[15, 20, 18, 25, 22, 30, 28, 35], color=colors.success, colors=colors)

    layout.addWidget(spark1)
    layout.addWidget(spark2)
    layout.addWidget(spark3)
    layout.addStretch()

    examples.append((
        "Sparklines",
        container,
        'SparkLine(values=[10, 15, 12, 18, ...])'
    ))

    return StoryPage(
        "Charts",
        "Data visualization charts using PyQtGraph.",
        examples,
        colors=colors
    )


def create_network_graph_story(colors: ColorPalette) -> StoryPage:
    """Network graph visualization story"""
    examples = []

    # Basic network graph
    graph = NetworkGraphWidget(title="Code Co-occurrence", height=300, colors=colors)

    # Add nodes
    graph.add_node(GraphNode("learning", "Learning", color=colors.code_yellow, size=40))
    graph.add_node(GraphNode("experience", "Experience", color=colors.success, size=35))
    graph.add_node(GraphNode("emotions", "Emotions", color=colors.code_pink, size=30))
    graph.add_node(GraphNode("goals", "Goals", color=colors.info, size=35))
    graph.add_node(GraphNode("challenges", "Challenges", color=colors.warning, size=25))

    # Add edges
    graph.add_edge(GraphEdge("learning", "experience", weight=5))
    graph.add_edge(GraphEdge("learning", "goals", weight=3))
    graph.add_edge(GraphEdge("experience", "emotions", weight=4))
    graph.add_edge(GraphEdge("goals", "challenges", weight=2))
    graph.add_edge(GraphEdge("emotions", "challenges", weight=3))

    graph.layout("spring")

    examples.append((
        "Network Graph",
        graph,
        'graph = NetworkGraphWidget(title="Co-occurrence")\n'
        'graph.add_node(GraphNode("id", "Label"))\n'
        'graph.add_edge(GraphEdge("a", "b", weight=5))\n'
        'graph.layout("spring")'
    ))

    return StoryPage(
        "Network Graph",
        "Interactive network graphs using NetworkX + QGraphicsScene.",
        examples,
        colors=colors
    )


def create_word_cloud_story(colors: ColorPalette) -> StoryPage:
    """Word cloud visualization story"""
    examples = []

    # Word cloud with frequencies
    wc = WordCloudWidget(
        title="Most Frequent Words",
        width=350,
        height=220,
        color_scheme="primary",
        colors=colors
    )
    wc.set_frequencies({
        "qualitative": 45,
        "research": 40,
        "coding": 38,
        "analysis": 35,
        "interview": 32,
        "participant": 30,
        "theme": 28,
        "data": 25,
        "pattern": 22,
        "category": 20,
        "memo": 18,
        "insight": 15,
        "experience": 14,
        "learning": 12,
        "emotion": 10,
    })
    examples.append((
        "Word Cloud",
        wc,
        'wc = WordCloudWidget(title="Frequent Words")\n'
        'wc.set_frequencies({"word": 45, ...})'
    ))

    # Rainbow color scheme
    wc_rainbow = WordCloudWidget(
        title="Rainbow Scheme",
        width=350,
        height=220,
        color_scheme="rainbow",
        colors=colors
    )
    wc_rainbow.set_frequencies({
        "learning": 40,
        "experience": 35,
        "emotions": 30,
        "goals": 28,
        "challenges": 25,
        "growth": 22,
        "support": 20,
        "motivation": 18,
    })
    examples.append((
        "Word Cloud (Rainbow)",
        wc_rainbow,
        'WordCloudWidget(color_scheme="rainbow")'
    ))

    return StoryPage(
        "Word Cloud",
        "Word cloud visualization using the wordcloud library.",
        examples,
        colors=colors
    )


def create_image_annotation_story(colors: ColorPalette) -> StoryPage:
    """Image annotation layer story"""
    examples = []

    # Annotation layer with sample image
    layer = ImageAnnotationLayer(show_toolbar=True, colors=colors)

    # Create a sample image
    pixmap = QPixmap(400, 250)
    pixmap.fill(QColor(colors.surface_lighter))
    layer.load_pixmap(pixmap)

    # Set to rectangle mode by default
    layer.set_mode(AnnotationMode.SELECT)

    examples.append((
        "Image Annotation Layer",
        layer,
        'layer = ImageAnnotationLayer()\n'
        'layer.load_image("/path/to/image.jpg")\n'
        'layer.set_mode(AnnotationMode.RECTANGLE)'
    ))

    return StoryPage(
        "Image Annotation",
        "Interactive image annotation with rectangles, polygons, and freehand drawing.",
        examples,
        colors=colors
    )


def create_heatmap_story(colors: ColorPalette) -> StoryPage:
    """Heat map visualization story"""
    examples = []

    # Heat map grid (co-occurrence matrix)
    grid = HeatMapGrid(
        row_labels=["Learning", "Experience", "Emotions", "Goals"],
        col_labels=["Learning", "Experience", "Emotions", "Goals"],
        values=[
            [1.0, 0.7, 0.4, 0.5],
            [0.7, 1.0, 0.6, 0.3],
            [0.4, 0.6, 1.0, 0.2],
            [0.5, 0.3, 0.2, 1.0],
        ],
        cell_size=45,
        color_scheme="primary",
        colors=colors
    )
    examples.append((
        "Heat Map Grid",
        grid,
        'grid = HeatMapGrid(\n'
        '    row_labels=["A", "B"],\n'
        '    col_labels=["A", "B"],\n'
        '    values=[[1.0, 0.5], [0.5, 1.0]]\n'
        ')'
    ))

    # Individual heat map cells
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.sm)

    for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        cell = HeatMapCell(value=val, size=50, colors=colors)
        layout.addWidget(cell)
    layout.addStretch()

    examples.append((
        "Heat Map Cells",
        container,
        'HeatMapCell(value=0.75, color_scheme="primary")'
    ))

    # Diverging color scheme
    container2 = QWidget()
    layout2 = QHBoxLayout(container2)
    layout2.setSpacing(SPACING.sm)

    for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        cell = HeatMapCell(value=val, size=50, color_scheme="diverging", colors=colors)
        layout2.addWidget(cell)
    layout2.addStretch()

    examples.append((
        "Diverging Scheme",
        container2,
        'HeatMapCell(value=0.5, color_scheme="diverging")'
    ))

    return StoryPage(
        "Heat Map",
        "Heat map cells for co-occurrence matrices and frequency tables.",
        examples,
        colors=colors
    )


def create_score_bars_story(colors: ColorPalette) -> StoryPage:
    """Relevance score bars story"""
    examples = []

    # Relevance score bars
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setSpacing(SPACING.md)

    for score, label in [(0.95, "Document 1"), (0.82, "Document 2"), (0.67, "Document 3"), (0.45, "Document 4")]:
        bar = RelevanceScoreBar(score=score, label=label, colors=colors)
        layout.addWidget(bar)

    examples.append((
        "Relevance Score Bars",
        container,
        'RelevanceScoreBar(score=0.85, label="Result")'
    ))

    # Confidence variant
    container2 = QWidget()
    layout2 = QVBoxLayout(container2)
    layout2.setSpacing(SPACING.md)

    for score, label in [(0.92, "High Confidence"), (0.65, "Medium"), (0.35, "Low Confidence")]:
        bar = RelevanceScoreBar(score=score, label=label, variant="confidence", colors=colors)
        layout2.addWidget(bar)

    examples.append((
        "Confidence Scores",
        container2,
        'RelevanceScoreBar(score=0.85, variant="confidence")'
    ))

    # Score indicators
    container3 = QWidget()
    layout3 = QHBoxLayout(container3)
    layout3.setSpacing(SPACING.xl)

    layout3.addWidget(ScoreIndicator(label="Relevance", score=0.87, colors=colors))
    layout3.addWidget(ScoreIndicator(label="Confidence", score=0.72, variant="confidence", colors=colors))
    layout3.addWidget(ScoreIndicator(label="Match", score=0.95, variant="match", colors=colors))
    layout3.addStretch()

    examples.append((
        "Score Indicators",
        container3,
        'ScoreIndicator(label="Relevance", score=0.87)'
    ))

    return StoryPage(
        "Score Bars",
        "Progress-style bars for displaying relevance and confidence scores.",
        examples,
        colors=colors
    )


def create_pdf_viewer_story(colors: ColorPalette) -> StoryPage:
    """PDF viewer story"""
    examples = []

    # PDF viewer with toolbar
    viewer = PDFPageViewer(show_toolbar=True, show_thumbnails=False, colors=colors)
    viewer.setMinimumSize(500, 400)

    examples.append((
        "PDF Page Viewer",
        viewer,
        'viewer = PDFPageViewer(show_toolbar=True)\n'
        'viewer.load_document("/path/to/doc.pdf")\n'
        'viewer.page_changed.connect(on_page_change)\n'
        'viewer.text_selected.connect(on_selection)'
    ))

    # PDF viewer with thumbnails
    viewer_thumbs = PDFPageViewer(show_toolbar=True, show_thumbnails=True, colors=colors)
    viewer_thumbs.setMinimumSize(600, 400)

    examples.append((
        "With Thumbnails",
        viewer_thumbs,
        'PDFPageViewer(show_toolbar=True, show_thumbnails=True)'
    ))

    return StoryPage(
        "PDF Viewer",
        "PDF document viewer with text selection overlay. "
        "Ctrl+Click and drag to select text regions. "
        "Requires PyMuPDF (pymupdf) to be installed.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all visualization stories"""
    return [
        ("charts", "Charts", create_charts_story(colors)),
        ("network", "Network Graph", create_network_graph_story(colors)),
        ("wordcloud", "Word Cloud", create_word_cloud_story(colors)),
        ("annotation", "Image Annotation", create_image_annotation_story(colors)),
        ("pdf", "PDF Viewer", create_pdf_viewer_story(colors)),
        ("heatmap", "Heat Map", create_heatmap_story(colors)),
        ("scores", "Score Bars", create_score_bars_story(colors)),
    ]
