# QualCoder v2

A modern reimagining of QualCoder - a qualitative data analysis application.

## Credits

This project is inspired by and builds upon the original [QualCoder](https://github.com/ccbogel/QualCoder) by Colin Curtain (ccbogel). QualCoder is an excellent open-source qualitative data analysis application written in Python that supports text, image, audio, and video coding with AI-enhanced features.

If you find this useful, please also consider supporting the original project:

<a href="https://www.buymeacoffee.com/ccbogelB" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

> **Note:** This is an independent community project building modern UI components inspired by QualCoder. We are not officially affiliated with the original QualCoder project but gratefully acknowledge their pioneering work in open-source qualitative data analysis.

---

## Design System

A clean, minimal design system for PyQt6 inspired by [shadcn/ui](https://ui.shadcn.com/).

## Features

- **3 themes**: Light, Dark, and Halla Health branded
- **Design tokens**: Colors, spacing, typography, border radius
- **Styled components**: Button, Input, Card, Badge, Alert, Avatar, Separator
- **Full QSS stylesheet**: Covers all common Qt widgets

## Quick Start

```bash
pip install PyQt6
python demo.py          # Light theme
python demo.py dark     # Dark theme
python demo.py halla    # Halla Health theme
```

## Usage

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from design_system import (
    get_theme, generate_stylesheet,
    Button, Input, Card, CardHeader, Badge, Alert
)

app = QApplication([])

# Apply theme
colors = get_theme("light")  # or "dark" or "halla"
app.setStyleSheet(generate_stylesheet(colors))

# Use components
window = QMainWindow()
btn = Button("Click me", variant="secondary")
card = Card()
card.add_widget(CardHeader("Title", "Description"))
# ...

window.show()
app.exec()
```

## Components

### Button
```python
Button("Label")                          # Primary
Button("Label", variant="secondary")     # Secondary
Button("Label", variant="outline")       # Outline
Button("Label", variant="ghost")         # Ghost
Button("Label", variant="destructive")   # Destructive
Button("Label", size="sm")               # Small
Button("Label", size="lg")               # Large
```

### Input
```python
email = Input("Enter email")
email.set_error(True)   # Show error state
email.is_error()        # Check error state
```

### Card
```python
card = Card(shadow=True)
card.add_widget(CardHeader("Title", "Optional description"))
card.add_widget(some_widget)
card.add_layout(some_layout)
```

### Badge
```python
Badge("New")                              # Default
Badge("Status", variant="success")        # Success
Badge("Warning", variant="warning")       # Warning
Badge("Error", variant="destructive")     # Destructive
```

### Alert
```python
Alert("Title", "Description")                     # Default
Alert("Success!", "Saved.", variant="success")    # Success
Alert("Error", "Failed.", variant="destructive")  # Error
```

### Label
```python
Label("Regular text")
Label("Heading", variant="title")
Label("Small text", variant="muted")
Label("Help text", variant="description")
```

## Customization

### Creating a Custom Theme

```python
from design_system import ColorPalette, generate_stylesheet

my_theme = ColorPalette(
    background="#FFFFFF",
    foreground="#1a1a1a",
    primary="#0066CC",
    primary_foreground="#FFFFFF",
    # ... all other colors
)

stylesheet = generate_stylesheet(my_theme)
app.setStyleSheet(stylesheet)
```

### Extending Components

```python
from design_system import Button, SPACING, TYPOGRAPHY

class IconButton(Button):
    def __init__(self, icon: str, text: str = "", parent=None):
        super().__init__(text, parent)
        # Add icon handling...
```

## File Structure

```
pyqt6_design_system/
├── design_system/
│   ├── __init__.py      # Package exports
│   ├── tokens.py        # Design tokens (colors, spacing, etc.)
│   ├── stylesheet.py    # QSS stylesheet generator
│   └── components.py    # Reusable UI components
├── demo.py              # Demo application
├── requirements.txt
└── README.md
```

## License

MIT - Use freely in your projects.

## Acknowledgments

- [QualCoder](https://github.com/ccbogel/QualCoder) - The original qualitative data analysis application by Colin Curtain
- [shadcn/ui](https://ui.shadcn.com/) - Design system inspiration

## Notes

- For commercial distribution, consider using PySide6 (LGPL) instead of PyQt6 (GPL/Commercial)
- The demo requires a display; use `-platform offscreen` for headless testing
