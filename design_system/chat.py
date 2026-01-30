"""
Chat/AI components
Message bubbles, typing indicators, and AI interface widgets
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QTimer, Qt, Signal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors, hex_to_rgba


class MessageBubble(QFrame):
    """
    Chat message bubble for user or assistant.

    Usage:
        user_msg = MessageBubble("Hello!", role="user")
        ai_msg = MessageBubble("Hi there! How can I help?", role="assistant")
    """

    def __init__(
        self,
        text: str,
        role: str = "user",  # "user" or "assistant"
        timestamp: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._role = role

        is_user = role == "user"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        if not is_user:
            layout.addStretch()

        # Bubble
        bubble = QFrame()
        bubble.setMaximumWidth(400)

        if is_user:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.primary};
                    border-radius: {RADIUS.lg}px;
                    border-bottom-right-radius: {RADIUS.xs}px;
                }}
            """)
            text_color = "white"
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border-radius: {RADIUS.lg}px;
                    border-bottom-left-radius: {RADIUS.xs}px;
                }}
            """)
            text_color = self._colors.text_primary

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        bubble_layout.setSpacing(SPACING.xs)

        # Message text
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"""
            color: {text_color};
            font-size: {TYPOGRAPHY.text_sm}px;
            line-height: 1.4;
        """)
        bubble_layout.addWidget(msg)

        # Timestamp
        if timestamp:
            ts = QLabel(timestamp)
            ts.setStyleSheet(f"""
                color: {hex_to_rgba(self._colors.primary_foreground, 0.70) if is_user else self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            ts.setAlignment(Qt.AlignmentFlag.AlignRight)
            bubble_layout.addWidget(ts)

        layout.addWidget(bubble)

        if is_user:
            layout.addStretch()


class TypingIndicator(QFrame):
    """
    Animated typing indicator for AI responses.

    Usage:
        typing = TypingIndicator()
        typing.start()
        # Later...
        typing.stop()
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._dots = []
        self._current = 0

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.lg}px;
                border-bottom-left-radius: {RADIUS.xs}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        layout.setSpacing(SPACING.xs)

        # Three dots
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: 10px;")
            self._dots.append(dot)
            layout.addWidget(dot)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def start(self):
        self.show()
        self._timer.start(300)

    def stop(self):
        self._timer.stop()
        self.hide()

    def _animate(self):
        for i, dot in enumerate(self._dots):
            if i == self._current:
                dot.setStyleSheet(f"color: {self._colors.primary}; font-size: 10px;")
            else:
                dot.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: 10px;")
        self._current = (self._current + 1) % 3


class CodeSuggestion(QFrame):
    """
    AI-suggested code chip.

    Usage:
        suggestion = CodeSuggestion("Learning", color="#FFC107", confidence=0.85)
        suggestion.clicked.connect(self.apply_code)
    """

    clicked = Signal()
    rejected = Signal()

    def __init__(
        self,
        code_name: str,
        color: str = None,
        confidence: float = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
            QFrame:hover {{
                border-color: {self._colors.primary};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.sm)

        # Color dot
        if color:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
            layout.addWidget(dot)

        # Code name
        name = QLabel(code_name)
        name.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
        layout.addWidget(name)

        # Confidence
        if confidence is not None:
            conf = QLabel(f"{int(confidence * 100)}%")
            conf.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
            layout.addWidget(conf)

        # Accept button
        accept = QPushButton("✓")
        accept.setFixedSize(20, 20)
        accept.setCursor(Qt.CursorShape.PointingHandCursor)
        accept.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.success};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
            }}
        """)
        accept.clicked.connect(self.clicked.emit)
        layout.addWidget(accept)

        # Reject button
        reject = QPushButton("✕")
        reject.setFixedSize(20, 20)
        reject.setCursor(Qt.CursorShape.PointingHandCursor)
        reject.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.error};
                color: white;
            }}
        """)
        reject.clicked.connect(self.rejected.emit)
        layout.addWidget(reject)


class QuickPrompts(QFrame):
    """
    Predefined prompt buttons.

    Usage:
        prompts = QuickPrompts([
            "Suggest codes for this text",
            "Summarize the document",
            "Find similar passages"
        ])
        prompts.prompt_clicked.connect(self.send_prompt)
    """

    prompt_clicked = Signal(str)

    def __init__(
        self,
        prompts: List[str],
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        for prompt in prompts:
            btn = QPushButton(prompt)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.md}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_lighter};
                    border-color: {self._colors.primary};
                }}
            """)
            btn.clicked.connect(lambda checked, p=prompt: self.prompt_clicked.emit(p))
            layout.addWidget(btn)

        layout.addStretch()


class ChatInput(QFrame):
    """
    Chat message input with send button.

    Usage:
        chat_input = ChatInput()
        chat_input.message_sent.connect(self.send_message)
    """

    message_sent = Signal(str)

    def __init__(
        self,
        placeholder: str = "Type a message...",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Input
        self._input = QTextEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setMaximumHeight(100)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QTextEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        layout.addWidget(self._input, 1)

        # Send button
        send = QPushButton("➤")
        send.setFixedSize(40, 40)
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        send.clicked.connect(self._send)
        layout.addWidget(send)

    def _send(self):
        text = self._input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self._input.clear()

    def focus(self):
        self._input.setFocus()


class AIReasoningPanel(QFrame):
    """
    Panel showing AI reasoning/explanation.

    Usage:
        panel = AIReasoningPanel(
            title="Why this code?",
            explanation="Based on keywords 'learning' and 'experience'..."
        )
    """

    def __init__(
        self,
        title: str = "AI Reasoning",
        explanation: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-left: 3px solid {self._colors.info};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Header
        header = QHBoxLayout()
        icon = QLabel("💡")
        icon.setStyleSheet(f"font-size: 16px;")
        header.addWidget(icon)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Explanation
        if explanation:
            exp = QLabel(explanation)
            exp.setWordWrap(True)
            exp.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
                line-height: 1.4;
            """)
            layout.addWidget(exp)


class ConfidenceScore(QFrame):
    """
    Confidence score display.

    Usage:
        score = ConfidenceScore(0.85, label="Match confidence")
    """

    def __init__(
        self,
        value: float,
        label: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_sm}px;")
            layout.addWidget(lbl)

        # Score bar
        bar_container = QFrame()
        bar_container.setFixedSize(60, 8)
        bar_container.setStyleSheet(f"""
            background-color: {self._colors.surface_lighter};
            border-radius: 4px;
        """)

        bar = QFrame(bar_container)
        width = int(60 * value)
        bar.setGeometry(0, 0, width, 8)

        if value >= 0.7:
            color = self._colors.success
        elif value >= 0.4:
            color = self._colors.warning
        else:
            color = self._colors.error

        bar.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        layout.addWidget(bar_container)

        # Percentage
        pct = QLabel(f"{int(value * 100)}%")
        pct.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px; font-weight: bold;")
        layout.addWidget(pct)
