# Layout & Animation

Layout constants, shadows, z-index layering, and animation timing tokens.

## Layout Constants

```python
from design_system import LAYOUT

LAYOUT.sidebar_width   # 300px — Default sidebar width
LAYOUT.toolbar_height  # 52px  — Toolbar height
LAYOUT.panel_min_width # 200px — Minimum panel width
```

### Usage

```python
from design_system import LAYOUT

sidebar.setFixedWidth(LAYOUT.sidebar_width)
toolbar.setFixedHeight(LAYOUT.toolbar_height)
panel.setMinimumWidth(LAYOUT.panel_min_width)
```

## Animation

```python
from design_system import ANIMATION

ANIMATION.duration_fast    # 150ms — Quick transitions
ANIMATION.duration_normal  # 250ms — Standard transitions
ANIMATION.duration_slow    # 400ms — Deliberate animations
ANIMATION.easing_default   # "ease-in-out"
```

### Animation Examples

```python
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from design_system import ANIMATION

# Fade animation
animation = QPropertyAnimation(widget, b"opacity")
animation.setDuration(ANIMATION.duration_normal)
animation.setEasingCurve(QEasingCurve.InOutQuad)
animation.setStartValue(0.0)
animation.setEndValue(1.0)
animation.start()
```

## Shadows

```python
from design_system import SHADOWS

SHADOWS.sm   # Small shadow — subtle elevation
SHADOWS.md   # Medium shadow — cards, panels
SHADOWS.lg   # Large shadow — modals, dropdowns
SHADOWS.xl   # Extra large — floating elements
```

### Shadow Values

| Token | Typical Use |
|-------|-------------|
| `sm` | Buttons, inputs |
| `md` | Cards, panels |
| `lg` | Dropdowns, popovers |
| `xl` | Modals, dialogs |

### Usage

```python
from design_system import SHADOWS

stylesheet = f"""
    QWidget.card {{
        {SHADOWS.md}
    }}

    QMenu {{
        {SHADOWS.lg}
    }}
"""
```

## Z-Index

Layer hierarchy for stacking overlapping elements:

```python
from design_system import ZINDEX

ZINDEX.dropdown  # 1000 — Dropdown menus
ZINDEX.modal     # 1050 — Modal dialogs
ZINDEX.popover   # 1060 — Popovers
ZINDEX.tooltip   # 1070 — Tooltips
ZINDEX.toast     # 1080 — Toast notifications
```

### Z-Index Hierarchy

```
Base content          0
Dropdowns          1000
Modals             1050
Popovers           1060
Tooltips           1070
Toasts             1080
```

### Usage

```python
from PySide6.QtWidgets import QWidget
from design_system import ZINDEX

# Ensure modal appears above dropdown
modal = QWidget()
modal.raise_()  # Qt handles z-ordering

# For manual CSS-based layering
stylesheet = f"""
    QWidget.modal {{
        z-index: {ZINDEX.modal};
    }}
"""
```

## Gradients

```python
from design_system import GRADIENTS

GRADIENTS.primary    # Primary color gradient
GRADIENTS.secondary  # Secondary color gradient
```

### Usage

```python
from design_system import GRADIENTS

stylesheet = f"""
    QPushButton.gradient {{
        background: {GRADIENTS.primary};
    }}
"""
```

## Complete Token Summary

| Category | Tokens | Purpose |
|----------|--------|---------|
| Colors | `COLORS`, `ColorPalette` | 60+ color properties |
| Spacing | `SPACING` | 4px–32px scale |
| Radius | `RADIUS` | 0px–9999px |
| Typography | `TYPOGRAPHY` | Fonts, sizes, weights |
| Layout | `LAYOUT` | Dimension constants |
| Animation | `ANIMATION` | Duration, easing |
| Shadows | `SHADOWS` | Elevation shadows |
| Z-Index | `ZINDEX` | Layer ordering |
| Gradients | `GRADIENTS` | Background gradients |
