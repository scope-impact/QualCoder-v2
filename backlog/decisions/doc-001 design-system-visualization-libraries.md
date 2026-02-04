---
id: doc-001
title: Design System Visualization Libraries
status: Accepted
date: '2026-01-29'
deciders: []
labels:
  - design-system
  - architecture
  - dependencies
---

## Context

QualCoder v2 requires visualization components for:
1. **Charts** - Code frequency, distributions, trends
2. **Network Graphs** - Code relationships, co-occurrences
3. **Word Clouds** - Text analysis visualization
4. **PDF Viewing** - Document coding with text selection
5. **Image Annotation** - Region-based coding on images

We evaluated libraries based on:
- **User Experience (40%)** - Interactivity, responsiveness, visual quality
- **Licensing (25%)** - Commercial-friendly (MIT/BSD/LGPL preferred)
- **Integration (20%)** - PyQt6/PySide6 compatibility
- **Maintenance (15%)** - Active development, community support

## Decision

### Accepted Libraries

| Component | Library | License | Rationale |
|-----------|---------|---------|-----------|
| **Charts** | PyQtGraph | MIT | Native Qt, 60fps, interactive zoom/pan, handles 1M+ points |
| **Network Graphs** | NetworkX + QGraphicsScene | BSD + LGPL | Official Qt example, full layout algorithms (spring, circular, planar) |
| **Word Clouds** | wordcloud | MIT | High quality output, mask support, actively maintained (v1.9.6) |
| **PDF Viewing** | Qt PDF (QPdfDocument) | LGPL | Native Qt6 module, built-in search, requires PySide6 |
| **Image Annotation** | QGraphicsScene (custom) | LGPL | Full control, native Qt, reference LabelMe for features |

### Secondary/Export Libraries

| Component | Library | License | Use Case |
|-----------|---------|---------|----------|
| Static Charts | Matplotlib | BSD | Publication-quality export, reports |

### Rejected Libraries

| Library | License | Rejection Reason |
|---------|---------|------------------|
| PyMuPDF | AGPL | Copyleft - requires open-source or commercial license ($) |
| qpageview | GPL-3.0 | Copyleft - incompatible with proprietary distribution |
| LabelMe | GPL-3.0 | Copyleft - use as reference only, not embed |
| PyQt6-Charts | GPL | Requires commercial license for closed-source |
| pyvis | BSD | Outputs HTML/JS - not native Qt integration |

## Consequences

### Positive

- **All primary libraries are MIT/BSD/LGPL** - No licensing concerns for commercial use
- **Native Qt integration** - Consistent UX, no web view dependencies
- **Active maintenance** - All libraries actively developed (2025-2026 releases)
- **PyQtGraph handles real-time data** - Essential for live coding statistics

### Negative

- **Qt PDF requires PySide6** - May need to evaluate PyQt6 → PySide6 migration
- **Custom image annotation** - More development effort vs. using LabelMe
- **NetworkX graphs require QGraphicsScene wrapper** - Custom widget needed

### Neutral

- **Matplotlib for export only** - Static rendering acceptable for reports
- **wordcloud is static** - Interactive word clouds not critical for UX

## Implementation

### Dependencies to Add

```toml
# pyproject.toml
[project.dependencies]
pyqtgraph = ">=0.13"      # MIT - charts, real-time plots
networkx = ">=3.0"        # BSD - graph algorithms, layouts
wordcloud = ">=1.9"       # MIT - word cloud generation
numpy = ">=1.24"          # BSD - required by pyqtgraph/wordcloud
matplotlib = ">=3.8"      # BSD - export/publication charts
```

### Design System Components to Create

| Component | Base Library | Priority |
|-----------|--------------|----------|
| `ChartWidget` | PyQtGraph | P1 |
| `NetworkGraphWidget` | NetworkX + QGraphicsScene | P1 |
| `WordCloudWidget` | wordcloud | P2 |
| `PDFPageViewer` | Qt PDF | P1 |
| `ImageAnnotationLayer` | QGraphicsScene | P1 |

### Related Tasks

- QC-019.05 Chart Components
- QC-019.06 Charts Screen
- QC-019.07 Network Graph View
- QC-019.08 Word Cloud Generator
- QC-007.11 Image Coding Screen
- QC-007.17 PDF Coding Screen

## PyQt6 vs PySide6 Consideration

| Aspect | PyQt6 | PySide6 |
|--------|-------|---------|
| License | GPL or Commercial ($550+) | LGPL (free for commercial) |
| Qt PDF | Needs separate license | Included, LGPL |
| API | Nearly identical | Nearly identical |
| Migration | - | ~1 day effort (import changes) |

**Recommendation:** Evaluate PySide6 migration in ADR-002 if commercial distribution is planned.

## References

- [PyQtGraph Documentation](https://www.pyqtgraph.org/)
- [NetworkX + Qt Example](https://doc.qt.io/qtforpython-6/examples/example_external_networkx.html)
- [wordcloud GitHub](https://github.com/amueller/word_cloud)
- [Qt PDF Licensing](https://doc.qt.io/qt-6/qtpdf-licensing.html)
- [PyMuPDF AGPL Discussion](https://github.com/pymupdf/PyMuPDF/discussions/971)
