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

## DiffHighlighter

Syntax highlighter for git diff output with theme support.

```python
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from design_system import get_colors, ColorPalette

class DiffHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for git diff output.
    Uses design system colors for theme support (git-cola inspired).
    """

    def __init__(self, colors: ColorPalette, document):
        super().__init__(document)
        self._colors = colors

        # Addition format (green)
        self._add_format = QTextCharFormat()
        self._add_format.setBackground(QColor(colors.diff_add_bg))
        self._add_format.setForeground(QColor(colors.diff_add_fg))

        # Deletion format (red)
        self._remove_format = QTextCharFormat()
        self._remove_format.setBackground(QColor(colors.diff_remove_bg))
        self._remove_format.setForeground(QColor(colors.diff_remove_fg))

        # Header format (blue, bold)
        self._header_format = QTextCharFormat()
        self._header_format.setForeground(QColor(colors.diff_header_fg))
        self._header_format.setFontWeight(QFont.Weight.Bold)

        # Hunk format (purple)
        self._hunk_format = QTextCharFormat()
        self._hunk_format.setForeground(QColor(colors.diff_hunk_fg))

    def highlightBlock(self, text: str):
        if text.startswith("+") and not text.startswith("+++"):
            self.setFormat(0, len(text), self._add_format)
        elif text.startswith("-") and not text.startswith("---"):
            self.setFormat(0, len(text), self._remove_format)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self._hunk_format)
        elif text.startswith(("diff ", "index ", "---", "+++")):
            self.setFormat(0, len(text), self._header_format)
```

### DiffHighlighter Line Types

| Prefix | Format | Description |
|--------|--------|-------------|
| `+` (not `+++`) | Green bg/fg | Added line |
| `-` (not `---`) | Red bg/fg | Removed line |
| `@@` | Purple | Hunk marker |
| `diff `, `index `, `---`, `+++` | Blue, bold | Header |

### Design System Colors

The highlighter uses these color tokens from `ColorPalette`:

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `diff_add_bg` | `#d2ffe4` | `#1a472a` | Added line background |
| `diff_add_fg` | `#1a7f37` | `#7ee787` | Added line text |
| `diff_remove_bg` | `#fee0e4` | `#5c2d2d` | Removed line background |
| `diff_remove_fg` | `#b35900` | `#ff7b72` | Removed line text |
| `diff_header_fg` | `#0550ae` | `#79c0ff` | Header text |
| `diff_hunk_fg` | `#6639ba` | `#a371f7` | Hunk marker text |

---

## DiffViewerDialog

Modal dialog for viewing diff between two VCS snapshots.

```python
from src.contexts.projects.presentation.dialogs import DiffViewerDialog

dialog = DiffViewerDialog(
    from_ref="abc123",
    to_ref="def456",
    diff_content=diff_text,
    colors=get_colors(),
    parent=main_window
)
dialog.exec()
```

### DiffViewerDialog Features

- **Syntax highlighted diff** - Uses DiffHighlighter for color coding
- **Ref info display** - Shows from/to commit SHAs
- **Stats summary** - Additions, deletions, files changed
- **Scrollable content** - For large diffs
- **Theme aware** - Uses design system colors

### DiffViewerDialog Properties

| Property | Type | Description |
|----------|------|-------------|
| `from_ref` | str | Source commit SHA |
| `to_ref` | str | Target commit SHA |
| `diff_content` | str | Git diff output text |
| `colors` | ColorPalette | Design system colors |

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
