# QualCoder v2 - AI4C Project Proposals (Q1 2026)

**Context:** Q1 2026 is the last quarter AI4C accepts projects. QualCoder v2 has already submitted one project. These are additional proposal ideas based on what the codebase already supports and what could be built within a realistic timeline.

---

## Proposal 1: AI-Augmented Qualitative Coding Pipeline

**One-liner:** An open-source pipeline where AI agents perform initial qualitative data coding and human researchers review, refine, and interpret.

### Problem
Qualitative coding is the most time-consuming phase of qualitative research. A single interview transcript (60 min) can take 4-8 hours to code manually. Research teams with 20-50 interviews face weeks of mechanical work before they can begin analysis.

### Solution
Build a complete **AI-first coding pipeline** within QualCoder v2 where:

1. **AI reads** all sources in a project via MCP tools (already exists: `list_sources`, `read_content`)
2. **AI generates** a preliminary codebook based on research questions and data (needs: semantic analysis, theme suggestion)
3. **AI applies** codes to all sources in batch (already exists: `batch_apply_codes` MCP tool)
4. **Human reviews** AI-coded segments in a purpose-built review interface (needs: review workflow UI)
5. **AI learns** from human corrections and refines subsequent coding (needs: feedback loop)

### What Already Exists in Codebase
- MCP server with HTTP transport on localhost (decision-005)
- `batch_apply_codes` command handler optimized for AI (reduced round-trips)
- Auto-coding with pattern matching (exact, contains, regex) with preview and undo
- EventBus/SignalBridge so AI changes appear live in GUI
- Trust layer design (Autonomous / Notify / Suggest / Require)

### What Would Be Built
- Semantic code suggestion engine (ChromaDB vector store infrastructure exists)
- AI review workflow screen (approve/reject/modify AI-applied codes)
- Codebook generation from research questions + data sample
- Feedback mechanism: human corrections improve AI accuracy on remaining data
- Metrics dashboard: agreement rate between AI and human coder

### Impact
- Reduces qualitative coding time by estimated 60-80%
- Maintains methodological rigor through human-in-the-loop review
- Free and open source - accessible to any researcher
- Works with local AI (Ollama) for data privacy

### Tech Partner Fit
Partners with expertise in: **NLP/LLM fine-tuning, qualitative research methods, educational technology**

---

## Proposal 2: Multi-Agent Collaborative Research Analysis

**One-liner:** Multiple specialized AI agents collaborate on qualitative data analysis, each handling different methodological tasks, orchestrated through QualCoder's event-driven architecture.

### Problem
Qualitative research involves multiple distinct analytical tasks: coding, theme identification, memo writing, cross-case comparison, and report generation. Currently, even with AI, these are performed sequentially by one agent or one person.

### Solution
Build an **agent orchestration layer** where specialized AI agents work in parallel:

- **Coder Agent** - Reads sources, applies codes based on codebook
- **Theme Agent** - Analyzes coded segments, identifies emerging themes, suggests code merges
- **Memo Agent** - Generates analytical memos connecting coded segments to theory
- **Case Agent** - Compares coding patterns across cases, identifies outliers
- **Report Agent** - Generates structured findings with evidence chains

All agents work through QualCoder's MCP tools, share the same project database, and their actions appear in the researcher's GUI in real-time.

### What Already Exists in Codebase
- Bounded contexts for each research domain (coding, cases, sources, projects)
- EventBus for cross-context event distribution
- MCP tools for coding (4), cases (4), projects (2)
- SignalBridge for real-time GUI updates from any event source
- Session management infrastructure in Agent Context design

### What Would Be Built
- Agent orchestration coordinator (task distribution, conflict resolution)
- Per-agent MCP sessions with separate trust configurations
- Theme detection and code merge suggestion tools
- Memo generation from coded segments
- Cross-case comparison analysis tools
- Agent activity panel showing what each agent is doing in real-time

### Impact
- Enables analysis of large qualitative datasets (100+ interviews) that would be impractical manually
- Each agent can be specialized (different LLM, different prompt strategy)
- Researcher maintains oversight through approval workflows
- Extensible: research community can add new agent types

### Tech Partner Fit
Partners with expertise in: **multi-agent systems, AI orchestration, research methodology platforms**

---

## Proposal 3: Privacy-Preserving AI for Sensitive Qualitative Data

**One-liner:** Fully offline, locally-run AI qualitative analysis for research involving sensitive populations (healthcare, refugees, minors, justice-involved).

### Problem
Qualitative research frequently involves highly sensitive data:
- Patient health narratives (HIPAA, GDPR)
- Refugee and asylum-seeker interviews (safety risks)
- Research with minors (COPPA, institutional requirements)
- Criminal justice and substance use studies (legal risks)

Institutional Review Boards (IRBs) and ethics committees increasingly restrict or prohibit sending research data to cloud AI services. This locks sensitive research out of AI-assisted analysis.

### Solution
QualCoder v2's desktop-first, MCP-on-localhost architecture is uniquely positioned for **fully local AI processing**:

1. **Local LLM** via Ollama (Llama, Mistral, etc.) - no data leaves the machine
2. **Local embeddings** for semantic search - ChromaDB runs embedded
3. **Air-gapped mode** - disable all network access, run entirely offline
4. **Audit trail** - every AI action logged as immutable domain event
5. **IRB compliance toolkit** - generate reports showing no data exfiltration

### What Already Exists in Codebase
- Desktop application (PySide6) - no cloud dependency
- MCP server on localhost:8765 - stays on machine
- SQLite database - local file, no server
- ChromaDB vector store (embedded mode) - local
- LLM provider infrastructure (`embedding_provider.py`, `llm_provider.py`, `vector_store.py`)
- Domain event system with full event history
- OpenTelemetry instrumentation (observability)

### What Would Be Built
- Ollama integration (connect local models via MCP)
- Air-gapped mode toggle (disable all external network calls)
- Local embedding model pipeline (sentence-transformers or similar)
- IRB compliance report generator (audit trail of all AI actions)
- Data sensitivity classification (flag PII in sources before AI processing)
- Performance optimization for consumer-grade hardware

### Impact
- Opens AI-assisted analysis to the most impactful research domains
- First open-source QDA tool with provably local AI processing
- Directly addresses the #1 blocker researchers cite for AI adoption: data privacy
- Applicable globally (no cloud infrastructure needed)

### Tech Partner Fit
Partners with expertise in: **privacy-preserving ML, healthcare IT, research ethics, on-device AI**

---

## Proposal 4: Democratizing Qualitative Research with AI (Global South Focus)

**One-liner:** Free, multilingual, AI-assisted qualitative research tool designed for researchers in low-resource settings.

### Problem
- Leading QDA tools cost $100-1,500/year per researcher
- Most qualitative research tools are English-only or have limited localization
- Cloud-dependent AI tools require reliable internet (unavailable in many research settings)
- Researchers in the Global South produce critical qualitative research (health, education, governance) but are locked out of modern tooling

### Solution
Extend QualCoder v2 to be a **fully localized, offline-capable, AI-assisted QDA tool** specifically designed for low-resource research environments:

1. **Multilingual UI** - Full localization framework (infrastructure exists in settings context)
2. **Multilingual AI coding** - AI agents that code in the source language (not just English)
3. **Offline-first** - Local AI models, local database, no internet required after setup
4. **Low hardware requirements** - Quantized models, efficient SQLite queries
5. **Community codebook sharing** - Researchers share codebooks for common research domains

### What Already Exists in Codebase
- `LanguagePreference` entity with ISO 639-1 codes
- `change_language` command handler
- Localization ADR (decision-003)
- SQLite (works everywhere, no server)
- Design system with accessibility considerations
- LGPL-3.0 license (free forever)

### What Would Be Built
- Full localization for 5-10 priority languages (Spanish, French, Portuguese, Arabic, Swahili, Hindi)
- Multilingual LLM prompting strategies for qualitative coding
- Codebook template library (health, education, governance research domains)
- Installation packaging for Windows/macOS/Linux (offline installer)
- Community contribution workflow for translations and codebooks
- Low-bandwidth sync for collaborative projects

### Impact
- Removes financial barrier to professional qualitative research tools
- Enables AI-assisted analysis in non-English research for the first time
- Supports offline use in field research settings
- Builds research capacity in underserved regions

### Tech Partner Fit
Partners with expertise in: **i18n/l10n, multilingual NLP, development sector technology, educational platforms**

---

## Proposal Comparison Matrix

| Dimension | Proposal 1: Coding Pipeline | Proposal 2: Multi-Agent | Proposal 3: Privacy | Proposal 4: Global South |
|-----------|:---:|:---:|:---:|:---:|
| **Builds on existing code** | High | Medium | High | Medium |
| **Technical novelty** | Medium | High | Medium | Medium |
| **Social impact** | Medium | Low | High | Very High |
| **Feasibility (Q1-Q2)** | High | Medium | High | Medium |
| **AI4C alignment** | High | High | High | Very High |
| **Tech partner appeal** | High | High | Medium | High |
| **Demo-ability** | High | High | Medium | Medium |
| **Research community need** | Very High | Medium | Very High | Very High |

---

## Recommendation

**For maximum AI4C fit**, consider submitting:

1. **Proposal 1 (AI Coding Pipeline)** as the primary - it's the most immediately demonstrable, builds heavily on existing code, and solves a real pain point that every qualitative researcher experiences.

2. **Proposal 3 (Privacy-Preserving)** or **Proposal 4 (Global South)** as the social-impact angle - these address systemic barriers and have strong narratives for funding bodies.

**For TTTR discussion** (finding a tech partner):
- Proposal 2 (Multi-Agent) would be the most attractive to a tech partner interested in cutting-edge agent orchestration
- Proposal 1 could appeal to an NLP/LLM company wanting to demonstrate practical applications

---

*Generated from codebase analysis of scope-impact/QualCoder-v2 on 2026-02-17*
