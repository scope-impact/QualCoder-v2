# Chat & AI Components

AI interface components for chat, suggestions, and reasoning.

## MessageBubble

Chat message display.

![Message Bubbles](images/message_bubbles.png)

```python
from design_system import MessageBubble

user_msg = MessageBubble(
    text="What codes are most frequent?",
    role="user",
    timestamp="10:30 AM"
)

assistant_msg = MessageBubble(
    text="The most frequent code is 'Theme A' with 15 occurrences.",
    role="assistant",
    timestamp="10:30 AM"
)
```

### MessageBubble Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | str | required | Message content |
| `role` | str | required | `"user"` or `"assistant"` |
| `timestamp` | str | `None` | Message timestamp |

---

## TypingIndicator

Animated typing indicator.

![Typing Indicator](images/typing_indicator.png)

```python
from design_system import TypingIndicator

indicator = TypingIndicator()
indicator.start()
# ... AI is thinking ...
indicator.stop()
```

### TypingIndicator Methods

| Method | Description |
|--------|-------------|
| `start()` | Start animation |
| `stop()` | Stop animation |

---

## ChatInput

Message input with send button.

![Chat Input](images/chat_input.png)

```python
from design_system import ChatInput

chat_input = ChatInput()
chat_input.message_sent.connect(lambda text: send_message(text))
```

### ChatInput Signals

| Signal | Description |
|--------|-------------|
| `message_sent(text)` | Message submitted |

---

## QuickPrompts

Quick prompt suggestion buttons.

```python
from design_system import QuickPrompts

prompts = QuickPrompts()
prompts.add_prompt("Summarize this document")
prompts.add_prompt("Find common themes")
prompts.add_prompt("Extract key quotes")

prompts.prompt_clicked.connect(lambda text: send_prompt(text))
```

### QuickPrompts Methods

| Method | Description |
|--------|-------------|
| `add_prompt(text)` | Add a prompt button |
| `clear()` | Remove all prompts |

### QuickPrompts Signals

| Signal | Description |
|--------|-------------|
| `prompt_clicked(text)` | Prompt selected |

---

## CodeSuggestion

AI code suggestion display.

![Code Suggestions](images/code_suggestions.png)

```python
from design_system import CodeSuggestion

suggestion = CodeSuggestion(
    code_name="Theme A",
    code_color="#FFC107",
    confidence=0.85,
    text_excerpt="relevant text from document..."
)

# Signals
suggestion.accepted.connect(lambda: apply_suggestion())
suggestion.rejected.connect(lambda: dismiss_suggestion())
```

### CodeSuggestion Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `code_name` | str | required | Suggested code name |
| `code_color` | str | required | Code color |
| `confidence` | float | required | Confidence score (0-1) |
| `text_excerpt` | str | `""` | Relevant text |

### CodeSuggestion Signals

| Signal | Description |
|--------|-------------|
| `accepted` | Suggestion accepted |
| `rejected` | Suggestion rejected |

---

## AIReasoningPanel

AI reasoning explanation.

```python
from design_system import AIReasoningPanel

panel = AIReasoningPanel()
panel.set_reasoning("Based on the context of...")
```

### AIReasoningPanel Methods

| Method | Description |
|--------|-------------|
| `set_reasoning(text)` | Set reasoning text |
| `clear()` | Clear reasoning |

---

## ConfidenceScore

Score visualization.

```python
from design_system import ConfidenceScore

score = ConfidenceScore(value=0.92, label="Confidence")
```

### ConfidenceScore Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `value` | float | required | Score (0-1) |
| `label` | str | `""` | Score label |

---

## Chat Interface Example

Complete AI chat interface:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from design_system import (
    Panel, MessageBubble, ChatInput, QuickPrompts,
    TypingIndicator, CodeSuggestion
)

class AIChatPanel(Panel):
    def __init__(self):
        super().__init__()

        # Message area
        self.scroll = QScrollArea()
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.scroll.setWidget(self.message_container)
        self.add_widget(self.scroll)

        # Typing indicator
        self.typing = TypingIndicator()
        self.typing.hide()
        self.add_widget(self.typing)

        # Quick prompts
        self.prompts = QuickPrompts()
        self.prompts.add_prompt("Summarize document")
        self.prompts.add_prompt("Find themes")
        self.prompts.add_prompt("Suggest codes")
        self.prompts.prompt_clicked.connect(self.send_message)
        self.add_widget(self.prompts)

        # Input
        self.input = ChatInput()
        self.input.message_sent.connect(self.send_message)
        self.add_widget(self.input)

    def send_message(self, text):
        # Add user message
        msg = MessageBubble(text=text, role="user")
        self.message_layout.addWidget(msg)

        # Show typing indicator
        self.typing.show()
        self.typing.start()

        # Send to AI and get response...
        # self.call_ai(text)

    def receive_response(self, text):
        # Hide typing
        self.typing.stop()
        self.typing.hide()

        # Add assistant message
        msg = MessageBubble(text=text, role="assistant")
        self.message_layout.addWidget(msg)

    def show_suggestion(self, suggestion_data):
        suggestion = CodeSuggestion(
            code_name=suggestion_data["code"],
            code_color=suggestion_data["color"],
            confidence=suggestion_data["confidence"],
            text_excerpt=suggestion_data["excerpt"]
        )
        suggestion.accepted.connect(
            lambda: self.apply_code(suggestion_data)
        )
        self.message_layout.addWidget(suggestion)
```
