# Dependencies

Required packages for the QualCoder Design System.

## Core Dependencies

| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| PySide6 | ≥6.5 | Qt widgets and layouts | Yes |
| qtawesome | ≥1.2 | Material Design Icons (mdi6) | Yes |

## Visualization Dependencies

| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| pyqtgraph | ≥0.13 | Charts and plotting | Yes |
| networkx | ≥3.0 | Graph algorithms | Yes |
| wordcloud | ≥1.9 | Word cloud generation | Yes |
| numpy | ≥1.24 | Numerical operations | Yes |

## Document Dependencies

| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| pymupdf | ≥1.23 | PDF rendering | Optional |

## Installation

### All Dependencies

```bash
pip install PySide6 qtawesome pyqtgraph networkx wordcloud numpy pymupdf
```

### Minimal Installation

```bash
pip install PySide6 qtawesome
```

### With pyproject.toml

```toml
[project]
dependencies = [
    "PySide6>=6.5",
    "qtawesome>=1.2",
    "pyqtgraph>=0.13",
    "networkx>=3.0",
    "wordcloud>=1.9",
    "numpy>=1.24",
]

[project.optional-dependencies]
pdf = ["pymupdf>=1.23"]
```

## Compatibility

### Python Version

- Python 3.10+ required
- Python 3.11+ recommended

### Platform Support

| Platform | Status |
|----------|--------|
| Windows | Supported |
| macOS | Supported |
| Linux | Supported |

### Qt Version

- PySide6 6.5+ (Qt 6.5+)
- Earlier versions may work but are untested

## Optional Features

### PDF Viewer

The `PDFPageViewer` component requires `pymupdf`:

```bash
pip install pymupdf
```

Without this package, PDF viewer components will raise an import error.

### Word Cloud

The `WordCloudWidget` requires `wordcloud`:

```bash
pip install wordcloud
```

### Network Graph

The `NetworkGraphWidget` requires `networkx`:

```bash
pip install networkx
```

## Troubleshooting

### PySide6 Installation Issues

On some systems, you may need to install additional Qt dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install libxcb-xinerama0
```

**macOS:**
```bash
brew install qt6
```

### qtawesome Icons Not Loading

Ensure qtawesome is properly installed:

```python
import qtawesome as qta
# Test icon loading
icon = qta.icon("mdi6.folder")
```

### PyQtGraph OpenGL Issues

If you encounter OpenGL errors with charts:

```python
import pyqtgraph as pg
pg.setConfigOption('useOpenGL', False)
```
