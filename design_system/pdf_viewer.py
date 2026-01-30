"""
PDF viewer component using PyMuPDF (fitz)
Material Design styled PDF viewer with text selection overlay
"""

from dataclasses import dataclass

from PySide6.QtCore import (
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors

# Try to import PyMuPDF
try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class PDFTextBlock:
    """Text block extracted from PDF page"""

    text: str
    rect: tuple[float, float, float, float]  # x0, y0, x1, y1
    page: int


@dataclass
class PDFSelection:
    """Selection data for PDF text"""

    page: int
    rect: tuple[float, float, float, float]  # x0, y0, x1, y1
    text: str = ""


class PDFPageViewer(QFrame):
    """
    PDF document viewer with page navigation and text selection.

    Renders PDF pages using PyMuPDF and displays them in a scrollable
    graphics view. Supports zoom, page navigation, and text selection
    overlay for qualitative coding.

    Usage:
        viewer = PDFPageViewer()
        viewer.load_document("/path/to/document.pdf")
        viewer.page_changed.connect(lambda p: print(f"Page: {p}"))
        viewer.text_selected.connect(lambda sel: print(f"Selected: {sel.text}"))

        # Navigate
        viewer.go_to_page(5)
        viewer.next_page()
        viewer.set_zoom(1.5)

    Signals:
        page_changed(page): Emitted when current page changes
        text_selected(PDFSelection): Emitted when text is selected
        document_loaded(page_count): Emitted when document loads
        zoom_changed(zoom): Emitted when zoom level changes
    """

    page_changed = Signal(int)
    text_selected = Signal(object)  # PDFSelection
    document_loaded = Signal(int)  # page_count
    zoom_changed = Signal(float)

    def __init__(
        self,
        show_toolbar: bool = True,
        show_thumbnails: bool = False,
        initial_zoom: float = 1.0,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._doc = None
        self._current_page = 0
        self._page_count = 0
        self._zoom = initial_zoom
        self._dpi = 150  # Render DPI
        self._selection_start = None
        self._selection_rect = None
        self._text_blocks: list[PDFTextBlock] = []

        self._setup_ui(show_toolbar, show_thumbnails)

    def _setup_ui(self, show_toolbar: bool, show_thumbnails: bool):
        """Initialize the UI components"""
        self.setStyleSheet(f"""
            PDFPageViewer {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        if show_toolbar:
            self._toolbar = self._create_toolbar()
            layout.addWidget(self._toolbar)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Thumbnail sidebar (optional)
        if show_thumbnails:
            self._thumbnail_panel = self._create_thumbnail_panel()
            content_layout.addWidget(self._thumbnail_panel)

        # PDF view
        self._view = PDFGraphicsView(colors=self._colors)
        self._view.selection_made.connect(self._on_selection)
        content_layout.addWidget(self._view, 1)

        layout.addLayout(content_layout, 1)

        # Show placeholder if PyMuPDF not available
        if not HAS_PYMUPDF:
            self._show_missing_dependency()

    def _create_toolbar(self) -> QFrame:
        """Create the PDF toolbar"""
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        toolbar.setFixedHeight(44)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Page navigation
        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
            }}
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(SPACING.sm, 2, SPACING.sm, 2)
        nav_layout.setSpacing(SPACING.xs)

        # Previous button
        self._prev_btn = self._create_nav_button("mdi6.chevron-left", "Previous page")
        self._prev_btn.clicked.connect(self.previous_page)
        nav_layout.addWidget(self._prev_btn)

        # Page input
        self._page_input = QSpinBox()
        self._page_input.setMinimum(1)
        self._page_input.setMaximum(1)
        self._page_input.setFixedWidth(50)
        self._page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: 2px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0;
            }}
        """)
        self._page_input.valueChanged.connect(lambda v: self.go_to_page(v - 1))
        nav_layout.addWidget(self._page_input)

        # Page total
        self._page_label = QLabel("/ 0")
        self._page_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        nav_layout.addWidget(self._page_label)

        # Next button
        self._next_btn = self._create_nav_button("mdi6.chevron-right", "Next page")
        self._next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self._next_btn)

        layout.addWidget(nav_frame)

        # Zoom controls
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
            }}
        """)
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(SPACING.sm, 2, SPACING.sm, 2)
        zoom_layout.setSpacing(SPACING.xs)

        # Zoom out
        zoom_out_btn = self._create_nav_button("mdi6.minus", "Zoom out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        # Zoom label
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(50)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        zoom_layout.addWidget(self._zoom_label)

        # Zoom in
        zoom_in_btn = self._create_nav_button("mdi6.plus", "Zoom in")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        layout.addWidget(zoom_frame)

        # Fit to width button
        fit_btn = self._create_nav_button("mdi6.fit-to-screen", "Fit to width")
        fit_btn.clicked.connect(self.fit_to_width)
        layout.addWidget(fit_btn)

        # Rotate button
        rotate_btn = self._create_nav_button("mdi6.rotate-right", "Rotate")
        rotate_btn.clicked.connect(self._rotate_page)
        layout.addWidget(rotate_btn)

        layout.addStretch()

        return toolbar

    def _create_nav_button(self, icon_name: str, tooltip: str) -> QPushButton:
        """Create a navigation button"""
        from .icons import Icon

        btn = QPushButton()
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
            }}
            QPushButton:pressed {{
                background-color: {self._colors.surface_light};
            }}
        """)

        # Add icon
        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        icon = Icon(
            icon_name, size=18, color=self._colors.text_secondary, colors=self._colors
        )
        btn_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        return btn

    def _create_thumbnail_panel(self) -> QFrame:
        """Create the thumbnail sidebar"""
        panel = QFrame()
        panel.setFixedWidth(120)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Scroll area for thumbnails
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._thumbnail_container = QWidget()
        self._thumbnail_layout = QVBoxLayout(self._thumbnail_container)
        self._thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        self._thumbnail_layout.setSpacing(SPACING.sm)
        self._thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._thumbnail_container)
        layout.addWidget(scroll)

        return panel

    def _show_missing_dependency(self):
        """Show message when PyMuPDF is not installed"""
        self._view.scene().clear()

        text = self._view.scene().addText(
            "PyMuPDF not installed.\n\n"
            "Install with: uv add pymupdf\n\n"
            "Or: pip install pymupdf",
            QFont("Roboto", 12),
        )
        text.setDefaultTextColor(QColor(self._colors.text_secondary))
        text.setPos(50, 50)

    def load_document(self, path: str) -> bool:
        """
        Load a PDF document.

        Args:
            path: Path to the PDF file

        Returns:
            True if document loaded successfully
        """
        if not HAS_PYMUPDF:
            return False

        try:
            self._doc = fitz.open(path)
            self._page_count = len(self._doc)
            self._current_page = 0

            # Update UI
            if hasattr(self, "_page_input"):
                self._page_input.setMaximum(self._page_count)
                self._page_input.setValue(1)
            if hasattr(self, "_page_label"):
                self._page_label.setText(f"/ {self._page_count}")

            # Render first page
            self._render_current_page()

            # Generate thumbnails if panel exists
            if hasattr(self, "_thumbnail_layout"):
                self._generate_thumbnails()

            self.document_loaded.emit(self._page_count)
            return True

        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False

    def _render_current_page(self):
        """Render the current page to the view"""
        if not self._doc or not HAS_PYMUPDF:
            return

        page = self._doc[self._current_page]

        # Render at specified DPI with zoom
        mat = fitz.Matrix(self._zoom * self._dpi / 72, self._zoom * self._dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to QImage
        img = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888
            if pix.n == 3
            else QImage.Format.Format_RGBA8888,
        )

        pixmap = QPixmap.fromImage(img)
        self._view.set_page(pixmap)

        # Extract text blocks for selection
        self._extract_text_blocks(page)

    def _extract_text_blocks(self, page):
        """Extract text blocks from page for selection"""
        if not HAS_PYMUPDF:
            return

        self._text_blocks = []
        blocks = page.get_text("blocks")

        for block in blocks:
            if len(block) >= 5 and block[6] == 0:  # Text block (not image)
                self._text_blocks.append(
                    PDFTextBlock(
                        text=block[4],
                        rect=(block[0], block[1], block[2], block[3]),
                        page=self._current_page,
                    )
                )

    def _generate_thumbnails(self):
        """Generate page thumbnails"""
        if not self._doc or not HAS_PYMUPDF:
            return

        # Clear existing thumbnails
        while self._thumbnail_layout.count():
            item = self._thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Generate thumbnail for each page
        for i in range(min(self._page_count, 50)):  # Limit to 50 pages
            page = self._doc[i]
            mat = fitz.Matrix(0.15, 0.15)  # Small scale for thumbnail
            pix = page.get_pixmap(matrix=mat)

            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
                if pix.n == 3
                else QImage.Format.Format_RGBA8888,
            )

            thumb = PDFThumbnail(
                QPixmap.fromImage(img),
                i + 1,
                selected=(i == self._current_page),
                colors=self._colors,
            )
            thumb.clicked.connect(lambda p=i: self.go_to_page(p))
            self._thumbnail_layout.addWidget(thumb)

    def go_to_page(self, page: int):
        """Navigate to a specific page (0-indexed)"""
        if not self._doc:
            return

        page = max(0, min(page, self._page_count - 1))
        if page != self._current_page:
            self._current_page = page
            self._render_current_page()

            if hasattr(self, "_page_input"):
                self._page_input.blockSignals(True)
                self._page_input.setValue(page + 1)
                self._page_input.blockSignals(False)

            # Update thumbnail selection
            if hasattr(self, "_thumbnail_layout"):
                for i in range(self._thumbnail_layout.count()):
                    item = self._thumbnail_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().set_selected(i == page)

            self.page_changed.emit(page)

    def next_page(self):
        """Go to the next page"""
        self.go_to_page(self._current_page + 1)

    def previous_page(self):
        """Go to the previous page"""
        self.go_to_page(self._current_page - 1)

    def set_zoom(self, zoom: float):
        """Set zoom level (1.0 = 100%)"""
        self._zoom = max(0.25, min(4.0, zoom))
        self._render_current_page()

        if hasattr(self, "_zoom_label"):
            self._zoom_label.setText(f"{int(self._zoom * 100)}%")

        self.zoom_changed.emit(self._zoom)

    def zoom_in(self):
        """Increase zoom by 25%"""
        self.set_zoom(self._zoom + 0.25)

    def zoom_out(self):
        """Decrease zoom by 25%"""
        self.set_zoom(self._zoom - 0.25)

    def fit_to_width(self):
        """Fit page to viewer width"""
        if not self._doc or not HAS_PYMUPDF:
            return

        page = self._doc[self._current_page]
        page_width = page.rect.width * self._dpi / 72
        view_width = self._view.viewport().width() - 40  # Padding

        new_zoom = view_width / page_width
        self.set_zoom(new_zoom)

    def _rotate_page(self):
        """Rotate the current page view by 90 degrees"""
        self._view.rotate(90)

    def _on_selection(self, rect: QRectF):
        """Handle selection from the graphics view"""
        if not self._doc or not HAS_PYMUPDF:
            return

        # Scale rect back to PDF coordinates
        scale = self._zoom * self._dpi / 72
        pdf_rect = (
            rect.x() / scale,
            rect.y() / scale,
            rect.right() / scale,
            rect.bottom() / scale,
        )

        # Find text in selection
        page = self._doc[self._current_page]
        selected_text = page.get_text("text", clip=fitz.Rect(*pdf_rect))

        selection = PDFSelection(
            page=self._current_page, rect=pdf_rect, text=selected_text.strip()
        )

        self.text_selected.emit(selection)

    @property
    def current_page(self) -> int:
        """Get current page number (0-indexed)"""
        return self._current_page

    @property
    def page_count(self) -> int:
        """Get total page count"""
        return self._page_count

    @property
    def zoom(self) -> float:
        """Get current zoom level"""
        return self._zoom

    def get_page_size(self) -> tuple[float, float] | None:
        """Get the size of the current page in points"""
        if not self._doc or not HAS_PYMUPDF:
            return None

        page = self._doc[self._current_page]
        return (page.rect.width, page.rect.height)

    def close_document(self):
        """Close the current document"""
        if self._doc:
            self._doc.close()
            self._doc = None
            self._page_count = 0
            self._current_page = 0
            self._view.scene().clear()


class PDFGraphicsView(QGraphicsView):
    """Graphics view for rendering PDF pages with selection support"""

    selection_made = Signal(QRectF)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._pixmap_item = None
        self._selection_rect = None
        self._selection_start = None
        self._is_selecting = False

        # Setup scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

    def set_page(self, pixmap: QPixmap):
        """Set the page pixmap to display"""
        self._scene.clear()

        # Add white background behind page
        self._scene.addRect(
            0,
            0,
            pixmap.width(),
            pixmap.height(),
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor("white")),
        )

        # Add page pixmap
        self._pixmap_item = self._scene.addPixmap(pixmap)

        # Add shadow effect
        shadow = self._scene.addRect(
            5,
            5,
            pixmap.width(),
            pixmap.height(),
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor(0, 0, 0, 30)),
        )
        shadow.setZValue(-1)

        self.setSceneRect(QRectF(-20, -20, pixmap.width() + 40, pixmap.height() + 40))

    def mousePressEvent(self, event: QMouseEvent):
        """Start selection on Ctrl+Click"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._is_selecting = True
            self._selection_start = self.mapToScene(event.pos())
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

            # Remove old selection rect
            if self._selection_rect:
                self._scene.removeItem(self._selection_rect)
                self._selection_rect = None
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Update selection rectangle"""
        if self._is_selecting and self._selection_start:
            current = self.mapToScene(event.pos())

            rect = QRectF(
                min(self._selection_start.x(), current.x()),
                min(self._selection_start.y(), current.y()),
                abs(current.x() - self._selection_start.x()),
                abs(current.y() - self._selection_start.y()),
            )

            if self._selection_rect:
                self._selection_rect.setRect(rect)
            else:
                self._selection_rect = self._scene.addRect(
                    rect,
                    QPen(QColor(self._colors.primary), 2),
                    QBrush(QColor(self._colors.primary + "40")),
                )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Complete selection"""
        if self._is_selecting:
            self._is_selecting = False
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

            if self._selection_rect:
                rect = self._selection_rect.rect()
                if rect.width() > 5 and rect.height() > 5:
                    self.selection_made.emit(rect)
                else:
                    self._scene.removeItem(self._selection_rect)
                    self._selection_rect = None

            self._selection_start = None
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """Zoom with Ctrl+Scroll"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def clear_selection(self):
        """Clear the current selection"""
        if self._selection_rect:
            self._scene.removeItem(self._selection_rect)
            self._selection_rect = None


class PDFThumbnail(QFrame):
    """Thumbnail widget for PDF page"""

    clicked = Signal()

    def __init__(
        self,
        pixmap: QPixmap,
        page_number: int,
        selected: bool = False,
        has_codes: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected = selected
        self._page_number = page_number

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Image
        img_label = QLabel()
        img_label.setPixmap(
            pixmap.scaled(
                100,
                130,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_label)

        # Page number
        num_label = QLabel(str(page_number))
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(num_label)

        # Coded indicator
        if has_codes:
            indicator = QFrame()
            indicator.setFixedSize(8, 8)
            indicator.setStyleSheet(f"""
                background-color: {self._colors.primary};
                border-radius: 4px;
            """)
            indicator.move(self.width() - 12, 4)

    def _update_style(self):
        """Update visual style based on selection state"""
        border = (
            f"2px solid {self._colors.primary}"
            if self._selected
            else "2px solid transparent"
        )
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: {border};
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                border-color: {self._colors.border};
            }}
        """)

    def set_selected(self, selected: bool):
        """Update selection state"""
        self._selected = selected
        self._update_style()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
