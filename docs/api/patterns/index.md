# Patterns

Common usage patterns and best practices for building with the QualCoder Design System.

## Overview

| Pattern | Description |
|---------|-------------|
| [Signals](signals.md) | Qt signal-based interactivity |
| [Theming](theming.md) | Color customization and themes |
| [Composition](composition.md) | Building complex layouts |

## Quick Reference

### Signal Connections

```python
button.clicked.connect(handler)
table.row_clicked.connect(lambda idx, data: handle(idx))
search.text_changed.connect(filter_results)
```

### Theme Switching

```python
from design_system import set_theme, get_theme

set_theme("dark")
current = get_theme()
```

### Container Composition

```python
card = Card()
card.add_widget(CardHeader(title="Section"))
card.add_widget(Label("Content"))
card.add_widget(Button("Action", variant="primary"))
```
