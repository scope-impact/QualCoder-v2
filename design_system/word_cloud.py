"""
Word cloud visualization component
Wraps wordcloud library with design system theming
"""

from typing import Dict, List, Optional, Callable
from io import BytesIO

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QColor

from wordcloud import WordCloud
import numpy as np

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class WordCloudWidget(QFrame):
    """
    Word cloud visualization with design system theming.

    Wraps the wordcloud library to generate and display word clouds
    with customizable color schemes and interactivity.

    Usage:
        wc = WordCloudWidget(title="Most Frequent Words")

        # From word frequencies
        wc.set_frequencies({
            "qualitative": 45,
            "research": 38,
            "coding": 32,
            "analysis": 28,
        })

        # Or from raw text
        wc.set_text("Your text content here...")

    Signals:
        word_clicked(word): Emitted when a word is clicked
        generated(): Emitted when word cloud is generated
    """

    word_clicked = pyqtSignal(str)
    generated = pyqtSignal()

    def __init__(
        self,
        title: str = "",
        width: int = 400,
        height: int = 300,
        color_scheme: str = "primary",
        max_words: int = 100,
        min_font_size: int = 10,
        max_font_size: int = 80,
        background_color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._width = width
        self._height = height
        self._color_scheme = color_scheme
        self._max_words = max_words
        self._min_font_size = min_font_size
        self._max_font_size = max_font_size
        self._background_color = background_color or self._colors.surface
        self._frequencies: Dict[str, float] = {}
        self._wordcloud: Optional[WordCloud] = None

        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup the widget UI"""
        self.setStyleSheet(f"""
            WordCloudWidget {{
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

        # Word cloud image display
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(self._width, self._height)
        self._image_label.setStyleSheet(f"""
            background-color: {self._background_color};
            border-radius: {RADIUS.md}px;
        """)
        layout.addWidget(self._image_label)

        # Placeholder text
        self._placeholder = QLabel("No data to display")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        self._image_label.setLayout(QVBoxLayout())
        self._image_label.layout().addWidget(self._placeholder)

    def _get_color_func(self) -> Callable:
        """Get color function based on color scheme"""
        schemes = {
            "primary": [self._colors.primary, self._colors.primary_light, self._colors.primary_dark],
            "secondary": [self._colors.secondary, self._colors.secondary_light, self._colors.secondary_dark],
            "rainbow": [
                self._colors.code_red,
                self._colors.code_orange,
                self._colors.code_yellow,
                self._colors.code_green,
                self._colors.code_blue,
                self._colors.code_purple,
            ],
            "warm": [
                self._colors.code_red,
                self._colors.code_orange,
                self._colors.code_yellow,
                self._colors.code_pink,
            ],
            "cool": [
                self._colors.code_blue,
                self._colors.code_cyan,
                self._colors.code_purple,
                self._colors.code_green,
            ],
            "semantic": [
                self._colors.primary,
                self._colors.secondary,
                self._colors.success,
                self._colors.info,
                self._colors.warning,
            ],
        }

        palette = schemes.get(self._color_scheme, schemes["primary"])

        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            # Use random color from palette
            idx = hash(word) % len(palette)
            return palette[idx]

        return color_func

    def set_frequencies(self, frequencies: Dict[str, float]):
        """
        Set word frequencies and generate cloud.

        Args:
            frequencies: Dict mapping words to their frequency/weight
        """
        self._frequencies = frequencies
        self._generate()

    def set_text(self, text: str, stopwords: List[str] = None):
        """
        Generate word cloud from raw text.

        Args:
            text: Raw text to analyze
            stopwords: Optional list of words to exclude
        """
        # Use wordcloud's built-in text processing
        wc = WordCloud(
            width=self._width,
            height=self._height,
            max_words=self._max_words,
            stopwords=set(stopwords) if stopwords else None,
        )
        self._frequencies = wc.process_text(text)
        self._generate()

    def _generate(self):
        """Generate the word cloud image"""
        if not self._frequencies:
            self._placeholder.show()
            return

        self._placeholder.hide()

        # Parse background color to RGB tuple
        bg_color = QColor(self._background_color)
        bg_rgb = (bg_color.red(), bg_color.green(), bg_color.blue())

        # Create word cloud
        self._wordcloud = WordCloud(
            width=self._width,
            height=self._height,
            max_words=self._max_words,
            min_font_size=self._min_font_size,
            max_font_size=self._max_font_size,
            background_color=bg_rgb,
            color_func=self._get_color_func(),
            prefer_horizontal=0.7,
            relative_scaling=0.5,
        ).generate_from_frequencies(self._frequencies)

        # Convert to QPixmap
        self._update_display()
        self.generated.emit()

    def _update_display(self):
        """Update the display with current word cloud"""
        if self._wordcloud is None:
            return

        # Get image as numpy array
        image_array = self._wordcloud.to_array()

        # Convert to QImage
        height, width, channel = image_array.shape
        bytes_per_line = 3 * width
        qimage = QImage(
            image_array.data,
            width, height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        # Convert to QPixmap and display
        pixmap = QPixmap.fromImage(qimage)
        self._image_label.setPixmap(pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def set_color_scheme(self, scheme: str):
        """
        Change the color scheme.

        Options: "primary", "secondary", "rainbow", "warm", "cool", "semantic"
        """
        self._color_scheme = scheme
        if self._frequencies:
            self._generate()

    def set_max_words(self, max_words: int):
        """Set maximum number of words to display"""
        self._max_words = max_words
        if self._frequencies:
            self._generate()

    def save_image(self, filepath: str):
        """Save word cloud as image file"""
        if self._wordcloud:
            self._wordcloud.to_file(filepath)

    def get_pixmap(self) -> Optional[QPixmap]:
        """Get the current word cloud as QPixmap"""
        return self._image_label.pixmap()

    def clear(self):
        """Clear the word cloud"""
        self._frequencies = {}
        self._wordcloud = None
        self._image_label.clear()
        self._placeholder.show()

    def resizeEvent(self, event):
        """Handle resize to update display"""
        super().resizeEvent(event)
        if self._wordcloud:
            self._update_display()


class WordCloudPreview(QLabel):
    """
    Compact word cloud preview widget.

    For use in thumbnails or previews where a smaller
    word cloud display is needed.

    Usage:
        preview = WordCloudPreview(size=QSize(150, 100))
        preview.set_frequencies({"word": 10, "cloud": 8})
    """

    def __init__(
        self,
        size: QSize = QSize(150, 100),
        color_scheme: str = "primary",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._size = size
        self._color_scheme = color_scheme

        self.setFixedSize(size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            background-color: {self._colors.surface_light};
            border-radius: {RADIUS.sm}px;
        """)

    def set_frequencies(self, frequencies: Dict[str, float]):
        """Generate and display word cloud from frequencies"""
        if not frequencies:
            return

        # Get color palette
        schemes = {
            "primary": [self._colors.primary, self._colors.primary_light],
            "secondary": [self._colors.secondary, self._colors.secondary_light],
        }
        palette = schemes.get(self._color_scheme, schemes["primary"])

        def color_func(word, **kwargs):
            return palette[hash(word) % len(palette)]

        bg_color = QColor(self._colors.surface_light)
        bg_rgb = (bg_color.red(), bg_color.green(), bg_color.blue())

        # Generate small word cloud
        wc = WordCloud(
            width=self._size.width(),
            height=self._size.height(),
            max_words=30,
            min_font_size=6,
            max_font_size=24,
            background_color=bg_rgb,
            color_func=color_func,
        ).generate_from_frequencies(frequencies)

        # Convert to QPixmap
        image_array = wc.to_array()
        height, width, _ = image_array.shape
        qimage = QImage(
            image_array.data,
            width, height,
            3 * width,
            QImage.Format.Format_RGB888
        )
        self.setPixmap(QPixmap.fromImage(qimage))
