# Document Components

Document display and editing components.

## TextPanel

Text document display with optional line numbers.

![Text Panel](images/text_panel.png)

```python
from design_system import TextPanel, LineNumberArea

panel = TextPanel(
    title="Interview Transcript",
    badge_text="Coded",
    show_header=True,
    editable=False,
    show_line_numbers=True
)

panel.set_text("Document content here...")
text = panel.get_text()
panel.set_stats([("Words", "1,234"), ("Codes", "15")])

panel.text_selected.connect(lambda text, start, end: print(f"Selected: {text}"))
```

### TextPanel Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `title` | str | `""` | Panel title |
| `badge_text` | str | `None` | Status badge |
| `show_header` | bool | `True` | Show header |
| `editable` | bool | `False` | Allow editing |
| `show_line_numbers` | bool | `True` | Show line numbers |

### TextPanel Methods

| Method | Description |
|--------|-------------|
| `set_text(text)` | Set document content |
| `get_text()` | Get document content |
| `set_stats(stats)` | Set stat pairs |

### TextPanel Signals

| Signal | Description |
|--------|-------------|
| `text_selected(text, start, end)` | Text selected |

---

## TranscriptPanel

Transcript display with segments.

![Transcript Panel](images/transcript_panel.png)

```python
from design_system import TranscriptPanel, TranscriptSegment

panel = TranscriptPanel()

# TranscriptSegment data class for transcript entries
panel.add_segment(TranscriptSegment(
    speaker="Interviewer",
    timestamp="00:00:15",
    text="Can you describe your experience?"
))
panel.add_segment(TranscriptSegment(
    speaker="Participant",
    timestamp="00:00:20",
    text="Well, I started by..."
))
```

### TranscriptSegment Data Class

```python
from design_system import TranscriptSegment

segment = TranscriptSegment(
    speaker="Speaker Name",
    timestamp="00:00:00",
    text="Segment content"
)
```

### TranscriptPanel Methods

| Method | Description |
|--------|-------------|
| `add_segment(segment)` | Add transcript segment |
| `clear()` | Clear all segments |

---

## SelectionPopup

Context popup for text selections.

```python
from design_system import SelectionPopup

popup = SelectionPopup()
popup.add_action("Apply Code", lambda: apply_code())
popup.add_action("Add Memo", lambda: add_memo())
popup.show_at(x, y)
```

### SelectionPopup Methods

| Method | Description |
|--------|-------------|
| `add_action(label, callback)` | Add action button |
| `show_at(x, y)` | Show at coordinates |
| `hide()` | Hide popup |

---

## TextColor

Text color class for text highlighting.

```python
from design_system import TextColor

color = TextColor(foreground="#000000", background="#FFFF00")
```

### TextColor Properties

| Property | Type | Description |
|----------|------|-------------|
| `foreground` | str | Text color |
| `background` | str | Background color |

---

## Document Viewer Example

Complete document viewer with coding:

```python
from design_system import (
    Panel, PanelHeader, TextPanel, SelectionPopup,
    CodeTree, Button
)

class DocumentViewer(Panel):
    def __init__(self):
        super().__init__()

        # Header
        self.add_widget(PanelHeader(title="Document"))

        # Text panel
        self.text_panel = TextPanel(
            show_header=True,
            editable=False,
            show_line_numbers=True
        )
        self.text_panel.text_selected.connect(self.on_selection)
        self.add_widget(self.text_panel)

        # Selection popup
        self.popup = SelectionPopup()
        self.popup.add_action("Apply Code", self.apply_code)
        self.popup.add_action("Add Memo", self.add_memo)

        self.selected_text = ""
        self.selection_range = (0, 0)

    def load_document(self, text, title="Document"):
        self.text_panel.set_text(text)

    def on_selection(self, text, start, end):
        self.selected_text = text
        self.selection_range = (start, end)

        # Show popup near selection
        cursor_pos = self.text_panel.cursor_position()
        self.popup.show_at(cursor_pos.x(), cursor_pos.y())

    def apply_code(self):
        self.popup.hide()
        # Open code selection dialog
        print(f"Apply code to: {self.selected_text}")

    def add_memo(self):
        self.popup.hide()
        # Open memo editor
        print(f"Add memo for: {self.selected_text}")
```
