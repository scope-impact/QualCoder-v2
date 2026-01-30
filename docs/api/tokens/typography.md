# Typography

Typography tokens define font families, sizes, and weights for consistent text styling.

## Font Families

```python
from design_system import TYPOGRAPHY

TYPOGRAPHY.font_family       # "Roboto"
TYPOGRAPHY.font_family_mono  # "Roboto Mono"
```

## Font Sizes

```python
from design_system import TYPOGRAPHY

TYPOGRAPHY.text_xs   # 10px — Captions, badges
TYPOGRAPHY.text_sm   # 12px — Secondary text, labels
TYPOGRAPHY.text_base # 14px — Body text (default)
TYPOGRAPHY.text_lg   # 16px — Emphasized text
TYPOGRAPHY.text_xl   # 18px — Subheadings
TYPOGRAPHY.text_2xl  # 24px — Headings
TYPOGRAPHY.text_3xl  # 28px — Page titles
```

## Font Weights

```python
from design_system import TYPOGRAPHY

TYPOGRAPHY.weight_normal    # 400 — Body text
TYPOGRAPHY.weight_medium    # 500 — Emphasized
TYPOGRAPHY.weight_semibold  # 600 — Subheadings
TYPOGRAPHY.weight_bold      # 700 — Headings
```

## Size Reference

| Token | Size | Typical Use |
|-------|------|-------------|
| `text_xs` | 10px | Badges, tooltips |
| `text_sm` | 12px | Labels, captions |
| `text_base` | 14px | Body text |
| `text_lg` | 16px | Lead paragraphs |
| `text_xl` | 18px | Section headers |
| `text_2xl` | 24px | Card titles |
| `text_3xl` | 28px | Page titles |

## Label Component

The `Label` component provides built-in typography variants:

```python
from design_system import Label

# Typography variants
title = Label("Main Title", variant="title")
description = Label("Some description", variant="description")
hint = Label("Optional field", variant="hint")
error = Label("Invalid input", variant="error")
muted = Label("Secondary info", variant="muted")
```

### Variant Mapping

| Variant | Size | Weight | Color |
|---------|------|--------|-------|
| `default` | base | normal | text_primary |
| `title` | 2xl | semibold | text_primary |
| `description` | base | normal | text_secondary |
| `hint` | sm | normal | text_hint |
| `error` | sm | normal | error |
| `muted` | sm | normal | text_disabled |
| `secondary` | base | normal | text_secondary |

## Usage Examples

### Custom Stylesheet

```python
from design_system import TYPOGRAPHY, COLORS

stylesheet = f"""
    QLabel {{
        font-family: {TYPOGRAPHY.font_family};
        font-size: {TYPOGRAPHY.text_base}px;
        color: {COLORS.text_primary};
    }}

    QLabel.title {{
        font-size: {TYPOGRAPHY.text_2xl}px;
        font-weight: {TYPOGRAPHY.weight_semibold};
    }}

    QLabel.code {{
        font-family: {TYPOGRAPHY.font_family_mono};
        font-size: {TYPOGRAPHY.text_sm}px;
    }}
"""
```

### Dynamic Sizing

```python
from design_system import TYPOGRAPHY

def get_heading_size(level: int) -> int:
    sizes = {
        1: TYPOGRAPHY.text_3xl,
        2: TYPOGRAPHY.text_2xl,
        3: TYPOGRAPHY.text_xl,
        4: TYPOGRAPHY.text_lg,
        5: TYPOGRAPHY.text_base,
        6: TYPOGRAPHY.text_sm,
    }
    return sizes.get(level, TYPOGRAPHY.text_base)
```
