# Spacing

Consistent spacing creates visual rhythm and hierarchy. The spacing scale uses a 4px base unit.

## Spacing Scale

```python
from design_system import SPACING

SPACING.xs    # 4px  — Tight spacing
SPACING.sm    # 8px  — Small gaps
SPACING.md    # 12px — Default spacing
SPACING.lg    # 16px — Comfortable spacing
SPACING.xl    # 20px — Large gaps
SPACING.xxl   # 24px — Section spacing
SPACING.xxxl  # 32px — Major sections
```

## Visual Reference

| Token | Value | Use Case |
|-------|-------|----------|
| `xs` | 4px | Icon padding, tight groups |
| `sm` | 8px | Button padding, list items |
| `md` | 12px | Card padding, form fields |
| `lg` | 16px | Section padding |
| `xl` | 20px | Card margins |
| `xxl` | 24px | Page sections |
| `xxxl` | 32px | Major layout gaps |

## Usage Examples

### Layout Margins

```python
from PySide6.QtWidgets import QVBoxLayout
from design_system import SPACING

layout = QVBoxLayout()
layout.setContentsMargins(
    SPACING.lg,  # left
    SPACING.lg,  # top
    SPACING.lg,  # right
    SPACING.lg   # bottom
)
layout.setSpacing(SPACING.md)
```

### Component Padding

```python
from design_system import SPACING

stylesheet = f"""
    QWidget {{
        padding: {SPACING.sm}px {SPACING.md}px;
    }}
"""
```

### Consistent Gaps

```python
from design_system import Card, Label, Button, SPACING

card = Card()
card.layout().setSpacing(SPACING.md)
card.add_widget(Label("Title"))
card.add_widget(Label("Description"))
card.add_widget(Button("Action"))
```

## Border Radius

The radius tokens complement spacing for consistent rounded corners:

```python
from design_system import RADIUS

RADIUS.none   # 0px   — Sharp corners
RADIUS.sm     # 4px   — Subtle rounding
RADIUS.md     # 8px   — Default rounding
RADIUS.lg     # 12px  — Prominent rounding
RADIUS.xl     # 16px  — Large rounding
RADIUS.full   # 9999px — Circular (pills, avatars)
```

### Radius Examples

```python
from design_system import RADIUS

# Button with default radius
button_style = f"border-radius: {RADIUS.md}px;"

# Circular avatar
avatar_style = f"border-radius: {RADIUS.full}px;"

# Sharp card
card_style = f"border-radius: {RADIUS.none}px;"
```
