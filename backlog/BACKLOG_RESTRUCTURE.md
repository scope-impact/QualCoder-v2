# QualCoder v2 Backlog - Big Picture

> **Purpose:** User-centric and Agent-centric feature backlog
> **Principle:** Every feature has a Human path AND an Agent path
> **Status:** DRAFT - Skeleton for Review

---

## The Two Actors

```
┌─────────────────────────────────────────────────────────────────────┐
│                        QualCoder v2                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐                         ┌─────────────┐           │
│   │ RESEARCHER  │                         │  AI AGENT   │           │
│   │   (Human)   │                         │ (Autonomous)│           │
│   └──────┬──────┘                         └──────┬──────┘           │
│          │                                       │                   │
│          │ Mouse/Keyboard                        │ tool_call         │
│          │ Visual Feedback                       │ MCP Protocol      │
│          ▼                                       ▼                   │
│   ┌──────────────────────────────────────────────────────┐          │
│   │                    EVENT BUS                          │          │
│   │  (Listens to Human Events AND Agent Events)          │          │
│   └──────────────────────────────────────────────────────┘          │
│          │                                       │                   │
│          ▼                                       ▼                   │
│   ┌─────────────┐                         ┌─────────────┐           │
│   │   Human     │                         │   Agent     │           │
│   │  Performed  │◄───── Same Domain ─────►│  Performed  │           │
│   │   Action    │        Logic            │   Action    │           │
│   └─────────────┘                         └─────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Trust Levels (Agent Autonomy)

| Level | Name | Description | Human Involvement |
|-------|------|-------------|-------------------|
| T1 | **Autonomous** | Agent acts freely | None - just notified |
| T2 | **Notify** | Agent acts, human informed | Post-action notification |
| T3 | **Suggest** | Agent proposes, human decides | Approval required |
| T4 | **Assist** | Human leads, agent helps | Human initiates |

---

## Parallel Development Tracks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWO PARALLEL DEVELOPMENT TRACKS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRACK A: RESEARCHER UI                    TRACK B: AGENT MCP               │
│  ─────────────────────                     ───────────────────              │
│                                                                             │
│  ┌─────────────────────┐                   ┌─────────────────────┐         │
│  │ Screens & Dialogs   │                   │ MCP Tools & Schemas │         │
│  │ (Qt/PySide6)        │                   │ (JSON-RPC/HTTP)     │         │
│  └──────────┬──────────┘                   └──────────┬──────────┘         │
│             │                                         │                     │
│             │         ┌───────────────────┐           │                     │
│             └────────►│  SHARED DOMAIN    │◄──────────┘                     │
│                       │  (Use Cases)      │                                 │
│                       │  - Coordinators   │                                 │
│                       │  - Repositories   │                                 │
│                       │  - Event Bus      │                                 │
│                       └───────────────────┘                                 │
│                                                                             │
│  Key Insight: Agent MCP tools can be developed IN PARALLEL with UI.        │
│  They share the same domain layer but have independent interfaces.          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Parallel Tracks Matter

| Without Parallel Tracks | With Parallel Tracks |
|------------------------|---------------------|
| Agent blocked until all UI screens done | Agent tools ship as domain is ready |
| MCP tools wait for Image/AV screens | Text MCP tools ship NOW |
| Testing requires full UI | Agent enables automated testing |
| Single critical path | Multiple parallel workstreams |

---

## Feature Map (Skeleton)

### F-000: Foundation (Architecture Setup)

> Establishes the base architecture that enables all other features.
> This is "done once" infrastructure - not user-facing, but enables everything.

| Component | Purpose | Status |
|-----------|---------|--------|
| Event Bus | Pub/sub for domain events | Done |
| Signal Bridge | Thread-safe domain → Qt signals | Done |
| Design System | Reusable UI components | Done |
| Result Type | Success/Failure pattern | Done |
| Typed IDs | CodeId, SourceId, etc. | Done |
| MCP Server | HTTP server for agent tools | Done |

---

### Core Features (What users DO)

| ID | Feature | Researcher Actions | Agent Actions | Trust |
|----|---------|-------------------|---------------|-------|
| **F-001** | **Open & Navigate Project** | Open project, browse sources, switch views | Navigate to specific source/segment | T1 |
| **F-002** | **Manage Sources** | Import files, organize, delete | Suggest imports, extract metadata | T3 |
| **F-003** | **Manage Codes** | Create codes, organize hierarchy, merge | Suggest new codes, detect duplicates | T3 |
| **F-004** | **Apply Codes to Text** | Select text, apply code, remove coding | Apply codes, suggest codes | T3 |
| **F-005** | **Apply Codes to Images** | Draw region, apply code | Detect regions, suggest codes | T3 |
| **F-006** | **Apply Codes to Audio/Video** | Mark time range, apply code | Transcribe, suggest codes | T3 |
| **F-007** | **Auto-Code** | Find patterns, batch apply | Find similar, batch apply | T2 |
| **F-008** | **Search & Find** | Search text, filter by code | Semantic search, find related | T1 |
| **F-009** | **Manage Cases** | Create cases, link sources | Suggest groupings | T3 |
| **F-010** | **Generate Reports** | Run reports, export | Generate summaries, insights | T2 |
| **F-011** | **Collaborate** | Switch coder, compare, merge | Detect conflicts, suggest resolutions | T3 |
| **F-012** | **Chat with Agent** | Ask questions, give instructions | Respond, execute tasks | T3 |

---

## Feature Details (Skeleton)

### F-001: Open & Navigate Project

**Researcher wants to:**
- Open an existing project or create new
- See list of sources in the project
- Navigate between different views (coding, analysis, etc.)
- Quickly find where they left off

**Agent wants to:**
- Know which project is active
- Navigate to a specific source or segment
- Understand current context for suggestions

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-001.1 | Open existing project | Researcher |
| F-001.2 | Create new project | Researcher |
| F-001.3 | View source list | Researcher |
| F-001.4 | Switch between screens | Researcher |
| F-001.5 | Get current project context | Agent |
| F-001.6 | Navigate to source | Agent |

---

### F-002: Manage Sources

**Researcher wants to:**
- Import text documents, PDFs, images, audio, video
- Organize sources into folders/groups
- View source properties and metadata
- Delete or archive sources

**Agent wants to:**
- List available sources
- Read source content
- Extract metadata automatically
- Suggest organization

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-002.1 | Import text document | Researcher |
| F-002.2 | Import PDF document | Researcher |
| F-002.3 | Import image files | Researcher |
| F-002.4 | Import audio/video files | Researcher |
| F-002.5 | Organize sources into folders | Researcher |
| F-002.6 | View source metadata | Researcher |
| F-002.7 | Delete source | Researcher |
| F-002.8 | List all sources | Agent |
| F-002.9 | Read source content | Agent |
| F-002.10 | Extract metadata | Agent |

---

### F-003: Manage Codes

**Researcher wants to:**
- Create new codes with name, color, description
- Organize codes into categories (hierarchy)
- Rename, recolor, edit codes
- Merge duplicate or similar codes
- Delete codes

**Agent wants to:**
- List available codes
- Suggest new codes based on content
- Detect potential duplicate codes
- Understand code hierarchy

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-003.1 | Create new code | Researcher |
| F-003.2 | Create code category | Researcher |
| F-003.3 | Move code to category | Researcher |
| F-003.4 | Rename code | Researcher |
| F-003.5 | Change code color | Researcher |
| F-003.6 | Edit code memo | Researcher |
| F-003.7 | Merge two codes | Researcher |
| F-003.8 | Delete code | Researcher |
| F-003.9 | List all codes | Agent |
| F-003.10 | Suggest new code | Agent |
| F-003.11 | Detect duplicate codes | Agent |

---

### F-004: Apply Codes to Text

**Researcher wants to:**
- Select text in a document
- Apply one or more codes to selection
- See highlighted coded segments
- View all segments for a code
- Remove coding from a segment
- Add memo to a segment

**Agent wants to:**
- Apply code to specific text positions
- Suggest codes for uncoded text
- List coded segments
- Find similar uncoded passages

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-004.1 | Select text and apply code | Researcher |
| F-004.2 | Apply multiple codes to selection | Researcher |
| F-004.3 | View coded segments with highlights | Researcher |
| F-004.4 | View all segments for a code | Researcher |
| F-004.5 | Remove coding from segment | Researcher |
| F-004.6 | Add memo to segment | Researcher |
| F-004.7 | Apply code to text range | Agent |
| F-004.8 | Suggest code for text | Agent |
| F-004.9 | List coded segments | Agent |
| F-004.10 | Find similar uncoded text | Agent |

---

### F-005: Apply Codes to Images

**Researcher wants to:**
- Draw rectangle/polygon on image
- Apply code to drawn region
- See coded regions as overlays
- Remove coding from region
- Add memo to region

**Agent wants to:**
- Detect objects/regions in image
- Apply code to image region
- Suggest codes for detected regions

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-005.1 | Draw region on image | Researcher |
| F-005.2 | Apply code to image region | Researcher |
| F-005.3 | View coded regions as overlays | Researcher |
| F-005.4 | Remove coding from region | Researcher |
| F-005.5 | Detect regions in image | Agent |
| F-005.6 | Apply code to detected region | Agent |
| F-005.7 | Suggest codes for image | Agent |

---

### F-006: Apply Codes to Audio/Video

**Researcher wants to:**
- Play audio/video with transcript
- Mark time range
- Apply code to time range
- See coded ranges on timeline
- Link to transcript text

**Agent wants to:**
- Transcribe audio/video
- Detect speakers
- Apply code to time range
- Suggest codes based on transcript

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-006.1 | Play media with transcript | Researcher |
| F-006.2 | Mark time range | Researcher |
| F-006.3 | Apply code to time range | Researcher |
| F-006.4 | View coded ranges on timeline | Researcher |
| F-006.5 | Transcribe media | Agent |
| F-006.6 | Detect speakers | Agent |
| F-006.7 | Apply code to time range | Agent |
| F-006.8 | Suggest codes from transcript | Agent |

---

### F-007: Auto-Code

**Researcher wants to:**
- Search for a text pattern
- See all matches highlighted
- Apply code to all matches at once
- Undo batch coding
- Auto-code by speaker

**Agent wants to:**
- Find similar passages to coded segment
- Batch apply codes to similar content
- Track and report auto-coding batches

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-007.1 | Search text pattern | Researcher |
| F-007.2 | Preview matches before coding | Researcher |
| F-007.3 | Apply code to all matches | Researcher |
| F-007.4 | Undo batch coding | Researcher |
| F-007.5 | Auto-code by speaker name | Researcher |
| F-007.6 | Find similar to coded segment | Agent |
| F-007.7 | Batch apply to similar | Agent |
| F-007.8 | Report batch results | Agent |

---

### F-008: Search & Find

**Researcher wants to:**
- Search text across all sources
- Filter by code, source, case
- Jump to search results
- Save search as smart collection

**Agent wants to:**
- Semantic search (meaning, not just text)
- Find related segments
- Answer questions about data

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-008.1 | Full-text search | Researcher |
| F-008.2 | Filter by code | Researcher |
| F-008.3 | Filter by source | Researcher |
| F-008.4 | Jump to result | Researcher |
| F-008.5 | Save search as collection | Researcher |
| F-008.6 | Semantic search | Agent |
| F-008.7 | Find related segments | Agent |
| F-008.8 | Answer data question | Agent |

---

### F-009: Manage Cases

**Researcher wants to:**
- Create case (e.g., participant)
- Link sources to case
- Add case attributes (demographics)
- View all data for a case

**Agent wants to:**
- List cases
- Suggest case groupings
- Compare across cases

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-009.1 | Create case | Researcher |
| F-009.2 | Link source to case | Researcher |
| F-009.3 | Add case attributes | Researcher |
| F-009.4 | View case data | Researcher |
| F-009.5 | List all cases | Agent |
| F-009.6 | Suggest case groupings | Agent |
| F-009.7 | Compare across cases | Agent |

---

### F-010: Generate Reports

**Researcher wants to:**
- Generate code frequency report
- Generate co-occurrence matrix
- Export coded data
- Visualize code distribution

**Agent wants to:**
- Generate summary of findings
- Identify themes and patterns
- Create visualizations

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-010.1 | Generate code frequencies | Researcher |
| F-010.2 | Generate co-occurrence matrix | Researcher |
| F-010.3 | Export to spreadsheet | Researcher |
| F-010.4 | Visualize code distribution | Researcher |
| F-010.5 | Summarize findings | Agent |
| F-010.6 | Identify themes | Agent |
| F-010.7 | Generate insight report | Agent |

---

### F-011: Collaborate

**Researcher wants to:**
- Switch between coders
- See who coded what
- Compare coding between coders
- Merge coding from multiple coders
- Calculate inter-rater reliability

**Agent wants to:**
- Detect coding conflicts
- Suggest conflict resolutions
- Calculate agreement statistics

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-011.1 | Switch coder identity | Researcher |
| F-011.2 | View coding by coder | Researcher |
| F-011.3 | Compare two coders | Researcher |
| F-011.4 | Merge coding | Researcher |
| F-011.5 | Calculate reliability | Researcher |
| F-011.6 | Detect conflicts | Agent |
| F-011.7 | Suggest resolutions | Agent |

---

### F-012: Chat with Agent

**Researcher wants to:**
- Ask questions about the data
- Give coding instructions
- Review agent suggestions
- Approve or reject agent actions

**Agent wants to:**
- Understand researcher intent
- Execute multi-step tasks
- Present findings clearly
- Learn from feedback

**Stories:**
| ID | Story | Actor |
|----|-------|-------|
| F-012.1 | Ask question about data | Researcher |
| F-012.2 | Give coding instruction | Researcher |
| F-012.3 | Review pending suggestions | Researcher |
| F-012.4 | Approve agent action | Researcher |
| F-012.5 | Reject agent action | Researcher |
| F-012.6 | Execute multi-step task | Agent |
| F-012.7 | Present findings | Agent |
| F-012.8 | Learn from feedback | Agent |

---

## Mapping: Old Structure → New Structure

| Old (Architecture) | New (User-Centric) |
|-------------------|-------------------|
| M-001: Foundation | Infrastructure - not a feature |
| M-002: Coding Context | F-003, F-004, F-007 |
| M-003: Source Management | F-002 |
| M-004: Case Management | F-009 |
| M-005: Analysis | F-008, F-010 |
| M-006: Agent Experience | F-012 |
| M-007: Collaboration | F-011 |

---

## Implementation Status Mapping

### Researcher UI Track

| Feature | Current Status | Notes |
|---------|---------------|-------|
| F-001 | Partial | Project open works, navigation partial |
| F-002 | Not Started | M-003 not started |
| F-003 | Done | QC-004 domain complete |
| F-004 | In Progress | QC-005/006/007 in progress |
| F-005 | Not Started | Part of QC-007 |
| F-006 | Not Started | Part of QC-007 |
| F-007 | In Progress | Auto-coding controller done |
| F-008 | Not Started | Part of M-005 |
| F-009 | Not Started | M-004 not started |
| F-010 | Not Started | M-005 not started |
| F-011 | Not Started | M-007 not started |
| F-012 | Partial | Agent infrastructure done |

### Agent MCP Track (Parallel Development)

| Feature | Agent Capability | Status |
|---------|------------------|--------|
| F-001 | Get project context | ✅ Done |
| F-001 | Navigate to source | ✅ Done |
| F-002 | List sources | ✅ Done |
| F-002 | Read source content | ✅ Done |
| F-002 | Extract metadata | ✅ Done |
| F-002 | **Add source** | ❌ Missing |
| F-003 | List codes | ✅ Done |
| F-003 | Get code details | ✅ Done |
| F-003 | **Create code** | ❌ Missing |
| F-004 | Apply codes | ✅ Done |
| F-004 | List segments | ✅ Done |
| F-004 | **Remove coding** | ❌ Missing |

**Key Blockers for Agent Testing:**
- Agent cannot create codes
- Agent cannot add test documents

---

## Next Steps

1. **Review this skeleton** - Does the feature breakdown make sense?
2. **Refine stories** - Add acceptance criteria (no implementation details)
3. **Prioritize** - Which features first?
4. **Track** - Map implementation to user stories

---

## Open Questions

1. Should Foundation (design system, event bus, etc.) be tracked as a feature or kept separate as "infrastructure"?

2. Are there missing features from the researcher's perspective?

3. Are there missing agent capabilities?

4. How granular should stories be? (Current: ~8-10 per feature)
