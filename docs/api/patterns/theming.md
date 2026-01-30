# Theming Patterns

Color customization and theme management.

## Theme Management

### Switch Themes

```python
from design_system import set_theme, get_theme

# Switch to dark theme
set_theme("dark")

# Switch to light theme
set_theme("light")

# Get current theme
current = get_theme()  # "light" or "dark"
```

### Apply Theme Stylesheet

```python
from design_system import generate_stylesheet, COLORS

# Generate and apply stylesheet
app.setStyleSheet(generate_stylesheet(COLORS))
```

## Custom Themes

### Register Custom Theme

```python
from design_system import ColorPalette, register_theme, set_theme

# Create custom palette
corporate_palette = ColorPalette(
    # Brand colors
    primary="#0066CC",
    primary_light="#3399FF",
    primary_dark="#004499",
    primary_hover="#0055AA",
    primary_foreground="#FFFFFF",

    secondary="#FF5722",
    secondary_light="#FF8A65",
    secondary_dark="#E64A19",

    # Semantic colors
    success="#4CAF50",
    success_light="#C8E6C9",
    warning="#FF9800",
    warning_light="#FFE0B2",
    error="#F44336",
    error_light="#FFCDD2",
    info="#2196F3",
    info_light="#BBDEFB",

    # Surface colors
    background="#FFFFFF",
    surface="#F5F5F5",
    surface_light="#FAFAFA",
    surface_elevated="#FFFFFF",

    # Text colors
    text_primary="#212121",
    text_secondary="#757575",
    text_disabled="#BDBDBD",
    text_hint="#9E9E9E",

    # Border colors
    border="#E0E0E0",
    border_light="#EEEEEE",
    divider="#E0E0E0",
)

# Register theme
register_theme("corporate", corporate_palette)

# Activate theme
set_theme("corporate")
```

## Component-Level Theming

### Pass Colors to Components

```python
from design_system import Button, COLORS, ColorPalette

# Use global colors (theme-aware)
button = Button("Save", variant="primary", colors=COLORS)

# Use custom colors for specific component
custom_colors = ColorPalette(primary="#FF5722")
special_button = Button("Special", variant="primary", colors=custom_colors)
```

### Override Specific Colors

```python
from design_system import COLORS

# Access themed colors
bg_color = COLORS.background
text_color = COLORS.text_primary

# Use in manual styling
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {bg_color};
        color: {text_color};
    }}
""")
```

## Dynamic Theme Switching

### React to Theme Changes

```python
from design_system import set_theme, generate_stylesheet, COLORS

class ThemeAwareApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.apply_theme("light")

    def toggle_theme(self):
        current = get_theme()
        new_theme = "dark" if current == "light" else "light"
        self.apply_theme(new_theme)

    def apply_theme(self, theme):
        set_theme(theme)
        self.setStyleSheet(generate_stylesheet(COLORS))
        # Notify child components if needed
        self.theme_changed.emit(theme)
```

### Theme-Aware Custom Widgets

```python
from design_system import COLORS

class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.update_style()

    def update_style(self):
        # Use current theme colors
        self.setStyleSheet(f"""
            CustomWidget {{
                background-color: {COLORS.surface};
                border: 1px solid {COLORS.border};
                border-radius: 8px;
            }}
            CustomWidget:hover {{
                background-color: {COLORS.surface_light};
            }}
        """)
```

## Color Utilities

### Conditional Styling

```python
from design_system import COLORS

def get_status_color(status: str) -> str:
    """Get color for status indicator."""
    return {
        "success": COLORS.success,
        "warning": COLORS.warning,
        "error": COLORS.error,
        "info": COLORS.info,
    }.get(status, COLORS.text_secondary)

def get_file_type_color(file_type: str) -> str:
    """Get color for file type icon."""
    return {
        "text": COLORS.file_text,
        "audio": COLORS.file_audio,
        "video": COLORS.file_video,
        "image": COLORS.file_image,
        "pdf": COLORS.file_pdf,
    }.get(file_type, COLORS.text_secondary)
```

### Color Manipulation

```python
def adjust_opacity(color: str, opacity: float) -> str:
    """Add opacity to hex color."""
    # Convert hex to rgba
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {opacity})"

# Usage
hover_bg = adjust_opacity(COLORS.primary, 0.1)
```

## Theme Best Practices

### Do

- Use design tokens instead of hardcoded colors
- Apply themes at the application level
- Update all components when theme changes
- Test both light and dark themes

### Don't

- Hardcode color values in components
- Mix themed and non-themed colors
- Ignore contrast ratios for accessibility
- Forget to update icons/images for themes
