# Quick Start

Build your first UI with the QualCoder Design System.

## Basic Import

```python
from design_system import (
    # Tokens
    COLORS, SPACING, RADIUS, TYPOGRAPHY, LAYOUT,
    ColorPalette, get_colors, get_theme,

    # Core
    Button, Input, Label, Card, Badge, Alert, Avatar, Chip,

    # Icons
    Icon, IconText, icon, get_pixmap, get_qicon,

    # Layout
    AppContainer, Panel, Sidebar, MainContent, Toolbar,

    # Forms
    SearchBox, Select, Textarea, ColorPicker,

    # Data
    DataTable, CodeTree, FileList,
)
```

## Creating Components

### Basic Button

```python
# Variants: primary, secondary, outline, ghost, danger, success, icon
button = Button("Click Me", variant="primary")
button.clicked.connect(lambda: print("Clicked!"))
```

### Text Input

```python
input_field = Input(placeholder="Enter name...")
input_field.textChanged.connect(lambda text: print(f"Text: {text}"))
```

### Card Container

```python
card = Card()
card.add_widget(Label("Title", variant="title"))
card.add_widget(Label("Description text", variant="description"))
card.add_widget(Button("Action", variant="primary"))
```

## Building a Form

```python
from PySide6.QtWidgets import QVBoxLayout, QWidget
from design_system import Card, Label, Input, Button, FormGroup

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        card = Card()

        # Header
        card.add_widget(Label("Login", variant="title"))

        # Form fields
        username_group = FormGroup(label="Username")
        username_group.add_widget(Input(placeholder="Enter username"))
        card.add_widget(username_group)

        password_group = FormGroup(label="Password")
        password_group.add_widget(Input(placeholder="Enter password"))
        card.add_widget(password_group)

        # Submit button
        card.add_widget(Button("Sign In", variant="primary"))

        layout.addWidget(card)
```

## Using Icons

```python
from design_system import Icon, IconText, Button

# Icon widget
folder_icon = Icon("mdi6.folder", size=24, color="#009688")

# Icon with text
file_item = IconText(icon="mdi6.file", text="document.txt")

# Button with icon
icon_button = Button("", variant="icon")
```

## Theme Management

```python
from design_system import set_theme, get_theme, COLORS

# Switch themes
set_theme("dark")
current = get_theme()  # "dark"

# Use themed colors
print(COLORS.primary)      # Automatically uses current theme
print(COLORS.background)   # Theme-aware background color
```

## Complete Example

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from design_system import (
    AppContainer, TitleBar, Toolbar, MainContent,
    Panel, Card, Label, Button, SearchBox,
    generate_stylesheet, COLORS
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QualCoder")
        self.resize(1200, 800)

        # Apply design system stylesheet
        self.setStyleSheet(generate_stylesheet(COLORS))

        # Create app container
        app = AppContainer()
        app.set_title_bar(TitleBar(title="QualCoder v2"))

        # Toolbar
        toolbar = Toolbar()
        toolbar.add_widget(SearchBox(placeholder="Search..."))
        app.set_toolbar(toolbar)

        # Main content
        content = MainContent()

        # Add a card
        card = Card()
        card.add_widget(Label("Welcome", variant="title"))
        card.add_widget(Label("Get started by importing files."))
        card.add_widget(Button("Import Files", variant="primary"))
        content.add_widget(card)

        app.set_content(content)
        self.setCentralWidget(app)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

## Next Steps

- [Design Tokens](../tokens/index.md) — Learn the color, spacing, and typography system
- [Core Components](../components/core.md) — Explore buttons, inputs, cards, and more
- [Patterns](../patterns/index.md) — Common usage patterns
