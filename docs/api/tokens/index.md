# Design Tokens

Design tokens are the foundation of the QualCoder Design System — consistent values for colors, spacing, typography, and layout that ensure visual coherence across all components.

## Overview

| Token | Module | Purpose |
|-------|--------|---------|
| `COLORS` | `tokens.py` | Color palette with 60+ properties |
| `SPACING` | `tokens.py` | Spacing scale (4px to 32px) |
| `RADIUS` | `tokens.py` | Border radius values |
| `TYPOGRAPHY` | `tokens.py` | Font families, sizes, weights |
| `LAYOUT` | `tokens.py` | Layout constants |
| `ANIMATION` | `tokens.py` | Animation durations and easing |
| `SHADOWS` | `tokens.py` | Shadow definitions |
| `ZINDEX` | `tokens.py` | Z-index layering |

## Quick Reference

```python
from design_system import (
    COLORS, SPACING, RADIUS, TYPOGRAPHY,
    LAYOUT, ANIMATION, SHADOWS, ZINDEX
)

# Colors
COLORS.primary          # Primary brand color
COLORS.background       # Page background
COLORS.text_primary     # Main text color

# Spacing
SPACING.sm              # 8px
SPACING.md              # 12px
SPACING.lg              # 16px

# Typography
TYPOGRAPHY.text_base    # 14px
TYPOGRAPHY.font_family  # "Roboto"

# Radius
RADIUS.md               # 8px
RADIUS.full             # 9999px (circular)
```

## Sections

- [Colors](colors.md) — Complete color system with theming
- [Spacing](spacing.md) — Spacing scale and usage
- [Typography](typography.md) — Font families, sizes, and weights
- [Layout & Animation](layout-animation.md) — Layout constants, shadows, z-index
