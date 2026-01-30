"""
StoryPage component for displaying component stories with code examples
"""

import re
from typing import List, Tuple

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from ..tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class StoryPage(QFrame):
    """Individual story page with component preview and code"""

    def __init__(
        self,
        title: str,
        description: str,
        examples: List[Tuple[str, QWidget, str]],  # [(name, widget, code), ...]
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.background};
            }}
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING.xxl, SPACING.xxl, SPACING.xxl, SPACING.xxl)
        layout.setSpacing(SPACING.xl)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_base}px;
            line-height: 1.5;
        """)
        layout.addWidget(desc_label)

        # Examples
        for name, widget, code in examples:
            example = self._create_example(name, widget, code)
            layout.addWidget(example)

        layout.addStretch()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_example(self, name: str, widget: QWidget, code: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Example name
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px {RADIUS.lg}px 0 0;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # Preview area
        preview = QFrame()
        preview.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                padding: {SPACING.lg}px;
            }}
        """)
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        preview_layout.addWidget(widget)
        layout.addWidget(preview)

        # Code section
        code_frame = QFrame()
        code_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1e1e2e;
                border-top: 1px solid {self._colors.border};
                border-radius: 0 0 {RADIUS.lg}px {RADIUS.lg}px;
            }}
        """)
        code_layout = QVBoxLayout(code_frame)
        code_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        # Syntax highlight the code
        highlighted_code = self._highlight_code(code)
        code_label = QLabel(highlighted_code)
        code_label.setTextFormat(Qt.TextFormat.RichText)
        code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_label.setStyleSheet(f"""
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.5;
            padding: {SPACING.sm}px;
            background: transparent;
        """)
        code_layout.addWidget(code_label)

        layout.addWidget(code_frame)

        return frame

    def _highlight_code(self, code: str) -> str:
        """Apply syntax highlighting to Python code"""
        # Colors for syntax highlighting
        keyword_color = "#c678dd"  # Purple
        string_color = "#98c379"   # Green
        function_color = "#61afef"  # Blue
        class_color = "#e5c07b"    # Yellow
        number_color = "#d19a66"   # Orange
        comment_color = "#5c6370"  # Gray
        default_color = "#abb2bf"  # Light gray

        # Escape HTML
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Keywords
        keywords = [
            "def", "class", "if", "else", "elif", "for", "while", "try", "except",
            "finally", "with", "import", "from", "as", "return", "yield", "lambda",
            "and", "or", "not", "in", "is", "True", "False", "None", "self"
        ]
        for kw in keywords:
            code = re.sub(
                rf'\b({kw})\b',
                f'<span style="color: {keyword_color};">\\1</span>',
                code
            )

        # Strings (single and double quotes)
        code = re.sub(
            r'(".*?"|\'.*?\')',
            f'<span style="color: {string_color};">\\1</span>',
            code
        )

        # Numbers
        code = re.sub(
            r'\b(\d+\.?\d*)\b',
            f'<span style="color: {number_color};">\\1</span>',
            code
        )

        # Function/method calls
        code = re.sub(
            r'\.([a-zA-Z_]\w*)\(',
            f'.<span style="color: {function_color};">\\1</span>(',
            code
        )

        # Class names (capitalized words after 'class' or in type hints)
        code = re.sub(
            r'\b([A-Z][a-zA-Z0-9_]*)\b(?!\s*=)',
            f'<span style="color: {class_color};">\\1</span>',
            code
        )

        # Comments
        code = re.sub(
            r'(#.*?)($|\n)',
            f'<span style="color: {comment_color}; font-style: italic;">\\1</span>\\2',
            code
        )

        # Wrap in pre-formatted span
        code = code.replace('\n', '<br>')
        return f'<span style="color: {default_color};">{code}</span>'
