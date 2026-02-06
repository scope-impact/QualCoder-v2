# Colors

The color system provides 60+ color properties organized into semantic categories, with built-in support for light and dark themes.

## ColorPalette

```python
from design_system import (
    COLORS, ColorPalette, get_colors, get_theme,
    set_theme, register_theme, COLORS_LIGHT, COLORS_DARK
)

# Use default colors (follows current theme)
button = Button("Save", colors=COLORS)

# Get default palette
colors = get_colors()

# Theme management
set_theme("light")  # or "dark"
current_theme = get_theme()

# Access theme-specific palettes directly
light_colors = COLORS_LIGHT
dark_colors = COLORS_DARK
```

## Color Categories

### Primary Colors

| Property | Description |
|----------|-------------|
| `primary` | Main brand color |
| `primary_light` | Lighter variant for hover states |
| `primary_dark` | Darker variant for pressed states |
| `primary_hover` | Hover state color |
| `primary_foreground` | Text color on primary background |

### Secondary Colors

| Property | Description |
|----------|-------------|
| `secondary` | Secondary brand color |
| `secondary_light` | Lighter variant |
| `secondary_dark` | Darker variant |
| `secondary_hover` | Hover state color |

### Semantic Colors

| Property | Description |
|----------|-------------|
| `success` | Success state (green) |
| `success_light` | Light success background |
| `warning` | Warning state (yellow/orange) |
| `warning_light` | Light warning background |
| `error` | Error state (red) |
| `error_light` | Light error background |
| `info` | Info state (blue) |
| `info_light` | Light info background |

### Surface Colors

| Property | Description |
|----------|-------------|
| `background` | Page background |
| `surface` | Card/panel background |
| `surface_light` | Slightly elevated surface |
| `surface_lighter` | More elevated surface |
| `surface_elevated` | Highest elevation surface |

### Text Colors

| Property | Description |
|----------|-------------|
| `text_primary` | Main text color |
| `text_secondary` | Secondary/muted text |
| `text_disabled` | Disabled text |
| `text_hint` | Hint/placeholder text |

### Border Colors

| Property | Description |
|----------|-------------|
| `border` | Default border color |
| `border_light` | Light border color |
| `divider` | Divider line color |

### File Type Colors

| Property | Description |
|----------|-------------|
| `file_text` | Text file icon color |
| `file_audio` | Audio file icon color |
| `file_video` | Video file icon color |
| `file_image` | Image file icon color |
| `file_pdf` | PDF file icon color |

### Code Highlighting

| Property | Description |
|----------|-------------|
| `code_yellow` | Keywords, classes |
| `code_red` | Strings |
| `code_green` | Comments |
| `code_purple` | Numbers |
| `code_blue` | Functions |
| `code_pink` | Operators |
| `code_orange` | Decorators |
| `code_cyan` | Built-ins |

### Diff Viewer Colors

Colors for git diff output highlighting, inspired by [git-cola](https://github.com/git-cola/git-cola).

| Property | Light Theme | Dark Theme | Description |
|----------|-------------|------------|-------------|
| `diff_add_bg` | `#d2ffe4` | `#1a472a` | Background for added lines |
| `diff_add_fg` | `#1a7f37` | `#7ee787` | Foreground for added lines |
| `diff_remove_bg` | `#fee0e4` | `#5c2d2d` | Background for removed lines |
| `diff_remove_fg` | `#b35900` | `#ff7b72` | Foreground for removed lines |
| `diff_header_fg` | `#0550ae` | `#79c0ff` | Headers (`diff --git`, `+++`, `---`) |
| `diff_hunk_fg` | `#6639ba` | `#a371f7` | Hunk markers (`@@`) |

#### Usage Example

```python
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat
from design_system import get_colors

class DiffHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        colors = get_colors()

        # Addition format
        self._add_format = QTextCharFormat()
        self._add_format.setBackground(QColor(colors.diff_add_bg))
        self._add_format.setForeground(QColor(colors.diff_add_fg))

        # Deletion format
        self._remove_format = QTextCharFormat()
        self._remove_format.setBackground(QColor(colors.diff_remove_bg))
        self._remove_format.setForeground(QColor(colors.diff_remove_fg))

    def highlightBlock(self, text: str):
        if text.startswith("+") and not text.startswith("+++"):
            self.setFormat(0, len(text), self._add_format)
        elif text.startswith("-") and not text.startswith("---"):
            self.setFormat(0, len(text), self._remove_format)
```

## Custom Themes

Register and use custom color themes:

```python
from design_system import ColorPalette, register_theme, set_theme

# Create custom palette
custom_palette = ColorPalette(
    primary="#0066CC",
    primary_light="#3399FF",
    primary_dark="#004499",
    secondary="#FF5722",
    background="#FFFFFF",
    surface="#F5F5F5",
    text_primary="#212121",
    text_secondary="#757575",
    border="#E0E0E0",
    success="#4CAF50",
    warning="#FF9800",
    error="#F44336",
    info="#2196F3",
    # ... other properties
)

# Register theme
register_theme("corporate", custom_palette)

# Activate theme
set_theme("corporate")
```

## Usage Examples

### Component with Colors

```python
from design_system import Button, COLORS

# Components automatically use current theme
button = Button("Save", variant="primary")

# Or pass colors explicitly
button = Button("Save", variant="primary", colors=COLORS)
```

### Manual Color Access

```python
from design_system import COLORS

# Use in stylesheets
stylesheet = f"""
    QWidget {{
        background-color: {COLORS.background};
        color: {COLORS.text_primary};
    }}
    QPushButton {{
        background-color: {COLORS.primary};
        border-radius: 4px;
    }}
"""
```

### Conditional Styling

```python
from design_system import COLORS

def get_status_color(status: str) -> str:
    return {
        "success": COLORS.success,
        "warning": COLORS.warning,
        "error": COLORS.error,
        "info": COLORS.info,
    }.get(status, COLORS.text_secondary)
```
