"""
Editor components
Code editors, rich text editors, and related widgets
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
    QTextFormat,
)

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class CodeEditor(QFrame):
    """
    Code editor with syntax highlighting and line numbers.

    Usage:
        editor = CodeEditor(language="python")
        editor.set_code("def hello():\\n    print('Hello')")
        editor.code_changed.connect(self.on_change)
    """

    code_changed = Signal(str)

    def __init__(
        self,
        language: str = "text",
        read_only: bool = False,
        show_line_numbers: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._language = language

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Line numbers
        if show_line_numbers:
            self._line_numbers = LineNumbers(colors=self._colors)
            layout.addWidget(self._line_numbers)

        # Editor
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(read_only)
        self._editor.setFont(QFont("Menlo", 12))
        self._editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.sm}px;
                selection-background-color: {self._colors.primary}40;
            }}
        """)
        self._editor.textChanged.connect(lambda: self.code_changed.emit(self._editor.toPlainText()))

        if show_line_numbers:
            self._editor.blockCountChanged.connect(self._update_line_numbers)
            self._editor.cursorPositionChanged.connect(self._highlight_current_line)

        layout.addWidget(self._editor, 1)

        # Apply syntax highlighting
        if language != "text":
            self._highlighter = SimpleSyntaxHighlighter(
                self._editor.document(),
                language,
                self._colors
            )

    def _update_line_numbers(self):
        if hasattr(self, '_line_numbers'):
            self._line_numbers.set_line_count(self._editor.blockCount())

    def _highlight_current_line(self):
        # Could highlight current line here
        pass

    def set_code(self, code: str):
        self._editor.setPlainText(code)

    def get_code(self) -> str:
        return self._editor.toPlainText()

    def set_read_only(self, read_only: bool):
        self._editor.setReadOnly(read_only)


class LineNumbers(QFrame):
    """
    Line number gutter for code editor.

    Usage:
        numbers = LineNumbers()
        numbers.set_line_count(100)
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._line_count = 1
        self._current_line = 1

        self.setFixedWidth(50)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._labels = []
        self._build()

    def _build(self):
        # Ensure we have enough labels
        while len(self._labels) < self._line_count:
            num = len(self._labels) + 1
            label = QLabel(str(num))
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setFixedHeight(19)  # Approximate line height
            self._style_label(label, num == self._current_line)
            self._labels.append(label)
            self._layout.addWidget(label)

        # Show/hide labels
        for i, label in enumerate(self._labels):
            label.setVisible(i < self._line_count)

    def _style_label(self, label: QLabel, is_current: bool):
        if is_current:
            label.setStyleSheet(f"""
                color: {self._colors.text_primary};
                font-family: 'Menlo';
                font-size: 12px;
                padding-right: 8px;
                font-weight: bold;
            """)
        else:
            label.setStyleSheet(f"""
                color: {self._colors.text_disabled};
                font-family: 'Menlo';
                font-size: 12px;
                padding-right: 8px;
            """)

    def set_line_count(self, count: int):
        self._line_count = max(1, count)
        self._build()

    def set_current_line(self, line: int):
        self._current_line = line
        for i, label in enumerate(self._labels):
            self._style_label(label, i + 1 == line)


class SimpleSyntaxHighlighter(QSyntaxHighlighter):
    """Basic syntax highlighter for common languages"""

    def __init__(self, document: QTextDocument, language: str, colors: ColorPalette):
        super().__init__(document)
        self._colors = colors
        self._language = language
        self._rules = self._build_rules()

    def _build_rules(self):
        rules = []

        # Common keywords by language
        keywords = {
            "python": ["def", "class", "if", "else", "elif", "for", "while", "try",
                      "except", "finally", "with", "import", "from", "as", "return",
                      "yield", "lambda", "and", "or", "not", "in", "is", "True", "False", "None"],
            "javascript": ["function", "const", "let", "var", "if", "else", "for", "while",
                          "try", "catch", "finally", "return", "class", "extends", "import",
                          "export", "from", "async", "await", "true", "false", "null", "undefined"],
        }

        lang_keywords = keywords.get(self._language, [])

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self._colors.code_purple))
        keyword_format.setFontWeight(700)

        for word in lang_keywords:
            rules.append((f"\\b{word}\\b", keyword_format))

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self._colors.code_green))
        rules.append((r'"[^"]*"', string_format))
        rules.append((r"'[^']*'", string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self._colors.text_disabled))
        comment_format.setFontItalic(True)
        rules.append((r"#.*$", comment_format))  # Python
        rules.append((r"//.*$", comment_format))  # JS

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self._colors.code_cyan))
        rules.append((r"\b\d+\.?\d*\b", number_format))

        return rules

    def highlightBlock(self, text: str):
        import re
        for pattern, fmt in self._rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class RichTextEditor(QFrame):
    """
    Rich text editor with formatting toolbar.

    Usage:
        editor = RichTextEditor()
        editor.set_html("<p>Hello <b>World</b></p>")
        editor.content_changed.connect(self.on_change)
    """

    content_changed = Signal(str)

    def __init__(
        self,
        show_toolbar: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        if show_toolbar:
            self._toolbar = EditorToolbar(colors=self._colors)
            self._toolbar.format_clicked.connect(self._apply_format)
            layout.addWidget(self._toolbar)

        # Editor
        self._editor = QTextEdit()
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        self._editor.textChanged.connect(lambda: self.content_changed.emit(self._editor.toHtml()))
        layout.addWidget(self._editor, 1)

    def _apply_format(self, format_type: str):
        cursor = self._editor.textCursor()

        if format_type == "bold":
            fmt = cursor.charFormat()
            fmt.setFontWeight(700 if fmt.fontWeight() != 700 else 400)
            cursor.mergeCharFormat(fmt)
        elif format_type == "italic":
            fmt = cursor.charFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            cursor.mergeCharFormat(fmt)
        elif format_type == "underline":
            fmt = cursor.charFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            cursor.mergeCharFormat(fmt)
        elif format_type == "strike":
            fmt = cursor.charFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            cursor.mergeCharFormat(fmt)

    def set_html(self, html: str):
        self._editor.setHtml(html)

    def get_html(self) -> str:
        return self._editor.toHtml()

    def set_plain_text(self, text: str):
        self._editor.setPlainText(text)

    def get_plain_text(self) -> str:
        return self._editor.toPlainText()


class EditorToolbar(QFrame):
    """
    Formatting toolbar for rich text editor.

    Usage:
        toolbar = EditorToolbar()
        toolbar.format_clicked.connect(self.apply_format)
    """

    format_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        # Format buttons
        buttons = [
            ("B", "bold", "Bold (Ctrl+B)"),
            ("I", "italic", "Italic (Ctrl+I)"),
            ("U", "underline", "Underline (Ctrl+U)"),
            ("S̶", "strike", "Strikethrough"),
        ]

        for label, action, tooltip in buttons:
            btn = self._create_btn(label, action, tooltip)
            layout.addWidget(btn)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {self._colors.border};")
        layout.addWidget(sep)

        # Alignment buttons
        align_buttons = [
            ("⬅", "align_left", "Align left"),
            ("⬌", "align_center", "Center"),
            ("➡", "align_right", "Align right"),
        ]

        for label, action, tooltip in align_buttons:
            btn = self._create_btn(label, action, tooltip)
            layout.addWidget(btn)

        layout.addStretch()

    def _create_btn(self, label: str, action: str, tooltip: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                border-radius: {RADIUS.sm}px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
            }}
            QPushButton:pressed {{
                background-color: {self._colors.primary}26;
            }}
        """)
        btn.clicked.connect(lambda: self.format_clicked.emit(action))
        return btn


class MemoEditor(QFrame):
    """
    Memo/note editor for annotations.

    Usage:
        memo = MemoEditor(title="Research Notes")
        memo.content_changed.connect(self.save_memo)
    """

    content_changed = Signal(str)
    save_clicked = Signal()

    def __init__(
        self,
        title: str = "Memo",
        content: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px {RADIUS.md}px 0 0;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: white;
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        save_btn.clicked.connect(self.save_clicked.emit)
        header_layout.addWidget(save_btn)

        layout.addWidget(header)

        # Editor
        self._editor = QTextEdit()
        self._editor.setPlainText(content)
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        self._editor.textChanged.connect(lambda: self.content_changed.emit(self._editor.toPlainText()))
        layout.addWidget(self._editor, 1)

    def set_content(self, content: str):
        self._editor.setPlainText(content)

    def get_content(self) -> str:
        return self._editor.toPlainText()


class DiffViewer(QFrame):
    """
    Side-by-side diff viewer.

    Usage:
        diff = DiffViewer()
        diff.set_content(original_text, modified_text)
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left panel (original)
        self._left_panel = self._create_panel("Original")
        layout.addWidget(self._left_panel, 1)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {self._colors.border};")
        layout.addWidget(sep)

        # Right panel (modified)
        self._right_panel = self._create_panel("Modified")
        layout.addWidget(self._right_panel, 1)

    def _create_panel(self, title: str) -> QFrame:
        panel = QFrame()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # Header
        header = QLabel(title)
        header.setStyleSheet(f"""
            background-color: {self._colors.surface_light};
            color: {self._colors.text_secondary};
            padding: {SPACING.sm}px {SPACING.md}px;
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            border-bottom: 1px solid {self._colors.border};
        """)
        panel_layout.addWidget(header)

        # Editor
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.sm}px;
                font-family: 'Menlo';
                font-size: 12px;
            }}
        """)
        panel_layout.addWidget(editor, 1)

        panel.editor = editor
        return panel

    def set_content(self, original: str, modified: str):
        self._left_panel.editor.setPlainText(original)
        self._right_panel.editor.setPlainText(modified)
