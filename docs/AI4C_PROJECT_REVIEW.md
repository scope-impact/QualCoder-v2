# QualCoder v2 - AI4C Project Review

**Date:** 2026-02-17
**Reviewer:** Claude (automated codebase review)
**Repository:** scope-impact/QualCoder-v2
**Version:** 0.2.0 (pre-beta)
**License:** LGPL-3.0

---

## 1. Executive Summary

QualCoder v2 is a **modern, open-source qualitative data analysis (QDA) desktop application** built with Python and PySide6/Qt. It is a ground-up reimagining of the original [QualCoder](https://github.com/ccbogel/QualCoder) by Colin Curtain, redesigned around a core innovation: **AI agents are first-class consumers of the application, equal to the human GUI**.

Rather than embedding a chatbot, QualCoder v2 exposes its entire domain (coding, source management, case analysis) via the **Model Context Protocol (MCP)**, allowing any external AI system (Claude Code, Gemini CLI, Ollama, etc.) to drive qualitative research workflows autonomously or collaboratively with the researcher.

**Key metrics:**
- 6 bounded contexts, 41 command handlers, 10+ MCP tools
- 180+ design system components with light/dark themes
- 11 E2E test suites with Allure reporting
- 156 backlog tasks (21 done, 133 planned)
- CI/CD pipeline with automated test reports on GitHub Pages

---

## 2. What Problem Does It Solve?

### The Gap in Qualitative Research Tooling

Qualitative data analysis (QDA) is a labor-intensive research methodology used across social sciences, healthcare, education, and policy research. Researchers manually read through interviews, field notes, and media, then "code" (tag/annotate) segments of data to identify themes and patterns.

**Current landscape problems:**
1. **Proprietary lock-in** - Leading tools (NVivo, ATLAS.ti, MAXQDA) are expensive ($100-1,500/year) and closed-source
2. **No meaningful AI integration** - Existing QDA tools treat AI as a bolt-on feature (embedded chatbots), not as a core interaction paradigm
3. **Single-user paradigm** - Tools assume a lone researcher clicking through menus, not a researcher collaborating with AI agents
4. **Limited extensibility** - Closed architectures prevent researchers from building custom analysis pipelines

### QualCoder v2's Approach

QualCoder v2 addresses these by:
- Being **free and open source** (LGPL-3.0)
- Treating **AI as a primary interface** alongside the GUI
- Using **protocol-based integration** (MCP) so researchers choose their preferred AI
- Building on **domain-driven design** for maintainability and extensibility

---

## 3. Architecture & Technical Innovation

### 3.1 AI-as-Tool-Consumer Architecture (Primary Innovation)

The most distinctive technical contribution is the **Agent Context Layer** - an architectural pattern where the desktop application acts as a **tool provider** to external AI systems rather than embedding AI internally.

```
                    ┌──────────────────────┐
                    │   External AI Agent   │
                    │  (Claude Code, etc.)  │
                    └──────────┬───────────┘
                               │ MCP JSON-RPC
                    ┌──────────▼───────────┐
                    │   Agent Context Layer  │
                    │  (Protocol Adapters,   │
                    │   Session Manager,     │
                    │   Trust/Permissions)   │
                    └──────────┬───────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │           Domain Core (Pure Functions)    │
          │  Coding │ Sources │ Cases │ Analysis      │
          └────────────────────┬────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   PySide6 Desktop UI   │
                    │  (Human Researcher)    │
                    └──────────────────────┘
```

**Why this matters:**
- The AI doesn't need a custom interface - it uses the same command handlers as the GUI
- Changes made by AI automatically appear in the GUI via the EventBus/SignalBridge
- Researchers maintain control through a configurable Trust Layer (Autonomous / Notify / Suggest / Require approval)
- Any MCP-compatible AI can integrate without QualCoder-specific adapters

### 3.2 Functional Domain-Driven Design

The codebase follows a rigorous DDD architecture with **6 bounded contexts**:

| Context | Purpose | Command Handlers | MCP Tools |
|---------|---------|:---:|:---:|
| **Coding** | Code creation, text/image/AV coding, categories, auto-code | 12 | 4 |
| **Sources** | Import text, PDF, images, audio/video; content extraction | 6 | - |
| **Cases** | Case management, attributes, source linking | 9 | 4 |
| **Projects** | Project lifecycle (create, open, close) | 3 | 2 |
| **Settings** | Theme, font, language, backup, AV coding config | 5 | - |
| **Folders** | Source organization into folder hierarchies | 6 | - |

**Domain purity enforced through:**
- **Invariants**: Pure predicates (`is_valid_code_name()`, `can_apply_code()`)
- **Derivers**: Pure functions producing events from commands + state
- **Events**: Immutable domain facts (`CodeCreated`, `SegmentCoded`)
- **OperationResult**: Rich return type with `success`, `data`, `error`, `suggestions`, `rollback_command`

### 3.3 Reactive UI via Signal Bridge

Domain events flow through a **SignalBridge** pattern that converts domain events into Qt signals for thread-safe, real-time UI updates:

```
AI Agent makes change → Command Handler → Domain Event → EventBus
                                                            │
                                           ┌────────────────┤
                                           ▼                ▼
                                    SignalBridge        Other Contexts
                                           │            (cross-context
                                           ▼             reactions)
                                      Qt Signal
                                           │
                                           ▼
                                   UI Updates Live
```

This means when an AI agent applies codes to research data, the human researcher sees the changes appear in real-time in the GUI.

### 3.4 Technology Stack

| Layer | Technology | License |
|-------|-----------|---------|
| UI Framework | PySide6 (Qt6) | LGPL-3.0 |
| Language | Python 3.11+ | - |
| Database | SQLite via SQLAlchemy 2.0 | MIT |
| AI Protocol | MCP (HTTP on localhost) | - |
| Vector Store | ChromaDB (embedded) | Apache 2.0 |
| Charts | PyQtGraph | MIT |
| Media | python-vlc | LGPL |
| Documents | pypdf, python-docx, odfpy | Various OSS |
| Testing | pytest + Allure | MIT |
| Observability | OpenTelemetry | Apache 2.0 |

---

## 4. Current Feature Status

### 4.1 Implemented (Done - 21/156 tasks)

| Feature Area | What Works |
|-------------|------------|
| **Project Management** | Create, open, close projects; project statistics |
| **Source Import** | Text files, PDFs (with extraction), images, audio/video |
| **Source Organization** | Folder hierarchies, metadata viewing, source navigation |
| **Code Management** | Create/rename/delete codes, color picker (16 presets + hex), categories, code merging, duplicate detection |
| **Text Coding** | Quick-mark (Q key), create code (N key), in-vivo coding (V), unmark (U), multiple overlapping codes |
| **Auto-Coding** | Pattern matching (exact/contains/regex), preview before apply, batch operations with undo |
| **AI Integration** | MCP server, batch code application, code listing/details, case management tools |
| **Settings** | Light/dark themes, font preferences, all settings dialog |
| **Design System** | 180+ reusable components, tokens, storybook browser |

### 4.2 Planned (To Do - 133 tasks)

| Feature Area | Planned Capabilities |
|-------------|---------------------|
| **Image Coding** | Region selection, annotation, zoom/pan |
| **A/V Coding** | Timeline coding, speaker detection, transcript sync |
| **PDF Coding** | Page-level region coding |
| **Search** | Full-text search, semantic search via embeddings |
| **Reports** | Frequency reports, co-occurrence matrices, visualizations |
| **Case Analysis** | Attribute-based grouping, cross-case comparison |
| **Collaboration** | Multi-coder support, inter-rater reliability (Cohen's kappa) |
| **AI Chat** | Natural language interface for agent interaction |
| **Visualizations** | Network graphs, word clouds, charts |
| **Import/Export** | REFI-QDA standard, CSV/Excel export |

### 4.3 Test Coverage

**11 E2E test suites** covering the implemented features:

| Test Suite | Features Covered |
|-----------|-----------------|
| `test_text_coding_e2e.py` | Code creation, text coding, quick-mark, overlapping |
| `test_open_navigate_project_e2e.py` | Project lifecycle, navigation, agent tools |
| `test_auto_code_e2e.py` | Pattern matching, batch apply, preview |
| `test_segment_management_e2e.py` | Overlapping codes, memos, segment tracking |
| `test_manage_sources_e2e.py` | Multi-format import, folders, metadata |
| `test_code_management_e2e.py` | Code CRUD, categories, merging |
| `test_case_manager_e2e.py` | Case management operations |
| `test_settings_e2e.py` | User preferences |
| `test_mcp_realtime_e2e.py` | MCP agent integration |
| `test_file_manager_e2e.py` | File browser |
| `test_main_e2e.py` | Application shell wiring |

All tests use **real SQLite databases** (no mocks), **Allure reporting** with business-readable stories, and run headlessly in CI (`QT_QPA_PLATFORM=offscreen`).

---

## 5. Differentiators for AI4C

### 5.1 Novel: AI-as-Equal-Consumer Pattern

No other QDA tool (open or proprietary) treats AI agents as equal-status consumers of the application domain. This is not "AI-assisted coding" - it's **AI-native qualitative research** where:
- AI agents can autonomously code entire datasets
- The researcher supervises and refines through the GUI
- Multiple AI agents can collaborate on the same project simultaneously
- Trust levels are configurable per-tool and per-agent

### 5.2 Open Standard Integration (MCP)

By using the **Model Context Protocol**, QualCoder v2 is not locked into any single AI vendor. Researchers can use:
- **Claude Code** (Anthropic) for sophisticated reasoning
- **Gemini CLI** (Google) for multimodal analysis
- **Ollama** for local, private, offline AI processing
- Any future MCP-compatible agent

This is particularly important for **research ethics and data sovereignty** - sensitive qualitative data (e.g., patient interviews) can stay local with on-device AI.

### 5.3 Open Source for Research Community

As LGPL-3.0 software:
- Free for all researchers regardless of institutional funding
- Extensible by the research methods community
- Auditable for research transparency and reproducibility
- Suitable for use in developing countries and underfunded programs

### 5.4 Functional Architecture for Reliability

The functional DDD approach (pure domain logic, immutable events, OperationResult pattern) makes the codebase:
- **Testable without mocks** - domain logic is pure functions
- **Auditable** - every change produces an immutable event trail
- **Extensible** - new bounded contexts follow the same pattern
- **Reliable** - no hidden state mutations

### 5.5 Comprehensive Design System

The 180+ component design system with scholarly aesthetic (ink-inspired colors, warm paper surfaces) positions QualCoder as a **professional research tool**, not just a developer project. Light and dark themes are implemented, accessibility is considered, and the storybook browser enables rapid UI development.

---

## 6. Potential AI4C Proposal Angles

Based on the codebase analysis, here are areas where new AI4C project iterations could focus:

### Angle A: AI-Powered Qualitative Research Methodology

**Focus:** Demonstrate how AI agents can accelerate qualitative analysis while maintaining methodological rigor.

**What exists:** Auto-coding, batch code application, MCP tools for coding operations
**What's needed:** Semantic search, AI-suggested themes, co-occurrence analysis, reliability metrics
**Innovation:** AI doesn't replace the researcher's interpretive work - it handles the labor-intensive mechanics (initial coding passes, pattern detection) while the researcher focuses on meaning-making

### Angle B: Multi-Agent Collaborative Coding

**Focus:** Multiple AI agents + human researchers working on the same qualitative dataset simultaneously.

**What exists:** EventBus architecture, MCP server, trust layer design
**What's needed:** Session management for multiple agents, conflict resolution, inter-coder reliability
**Innovation:** First QDA tool where a team of AI agents can divide work (one codes interviews, another identifies themes, a third generates reports) with human oversight

### Angle C: Privacy-Preserving AI for Sensitive Research Data

**Focus:** Qualitative research often involves sensitive data (healthcare, vulnerable populations). QualCoder's architecture supports fully local AI processing.

**What exists:** Desktop-first architecture, MCP on localhost
**What's needed:** Ollama integration testing, local embedding models, offline-capable vector store
**Innovation:** Researchers can use AI assistance on sensitive data without any cloud transmission - important for IRB/ethics compliance

### Angle D: AI-Accessible Research Tools for Global South

**Focus:** Free, open-source QDA tool with AI assistance, accessible to researchers in resource-constrained settings.

**What exists:** LGPL license, multi-language infrastructure, SQLite (no server needed)
**What's needed:** Localization, low-bandwidth optimization, offline AI capabilities
**Innovation:** Democratizing access to AI-powered research tools that currently cost $100-1,500/year

---

## 7. Maturity Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Architecture** | Strong | Professional DDD, clean bounded contexts, event-driven |
| **Code Quality** | Strong | Consistent patterns, type hints, linting, pre-commit hooks |
| **Test Coverage** | Good | 11 E2E suites, but only for implemented features (~13%) |
| **Documentation** | Good | Architecture docs, user manual, component docs, skills |
| **Feature Completeness** | Early | 13% done (21/156 tasks), core MVP only |
| **AI Integration** | Foundational | MCP server works, tools exist, but chat/multi-agent pending |
| **UI Polish** | Good | Design system mature, but advanced screens not yet built |
| **Production Readiness** | Pre-beta | Solid foundations, but missing error handling, data safety |

**Overall:** QualCoder v2 has **enterprise-grade foundations** with a **clear, ambitious roadmap**. The architecture is its greatest strength - it's built to scale. The gap is primarily in feature completion, not quality.

---

## 8. Recommendations

1. **For AI4C proposal**: Lead with the AI-as-Equal-Consumer architecture - this is genuinely novel in the QDA space and aligns directly with AI4C's mission
2. **Quick wins for demo**: Semantic search (ChromaDB infrastructure exists) and AI-suggested themes would make compelling demonstrations
3. **For TTTR discussion**: The multi-agent collaboration angle could attract a tech partner interested in agent orchestration
4. **Risk mitigation**: The 13% completion rate may concern reviewers - consider scoping proposals around specific bounded contexts that are closer to complete (coding context is most mature)

---

*This review was generated from automated codebase analysis. All file paths and metrics are derived from the repository as of 2026-02-17.*
