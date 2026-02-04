# Installation

## Requirements

- Python 3.11+
- PySide6 6.5+
- [UV](https://docs.astral.sh/uv/) (recommended)

## Install with UV

```bash
git clone https://github.com/scope-impact/qualcoder-v2
cd qualcoder-v2
uv sync
```

## Install from PyPI

```bash
uv add qualcoder-design-system
# or
pip install qualcoder-design-system
```

## Dependencies

The design system automatically installs these dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.5 | Qt widgets and layouts |
| qtawesome | ≥1.2 | Material Design Icons (mdi6) |
| pyqtgraph | ≥0.13 | Charts and plotting |
| networkx | ≥3.0 | Graph algorithms |
| wordcloud | ≥1.9 | Word cloud generation |
| numpy | ≥1.24 | Numerical operations |
| pymupdf | ≥1.23 | PDF rendering |

## Verify Installation

```python
from design_system import Button, COLORS

# Should print the primary color
print(COLORS.primary)

# Create a test button
button = Button("Test", variant="primary")
print(f"Button created: {button}")
```

## IDE Setup

For best development experience, ensure your IDE recognizes the type annotations:

### VS Code

Install the Pylance extension for full type support.

### PyCharm

Type hints work out of the box.

## Next Steps

- [Quick Start](quick-start.md) — Build your first UI
- [Design Tokens](../tokens/index.md) — Learn the token system
