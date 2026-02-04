# QualCoder v2 Backlog Dependency Analysis

## Overview

**Total:** 20 features (QC-026 to QC-045) with 135+ subtasks

## Dependency Tiers

```
TIER 1: FOUNDATION (Must complete first)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-026: Open & Navigate Project                                    │
│  └── Entry point - blocks EVERYTHING                                │
│                                                                     │
│  QC-027: Manage Sources                                             │
│  └── Imports text/image/AV/PDF - blocks all coding features         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
TIER 2: CORE CODING (Text - mostly done ✓)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-028: Manage Codes ────────────────────────────── [In Progress]  │
│  ├── Researcher: create, organize, merge codes ✓                    │
│  └── Agent: list, suggest, create codes                             │
│                                                                     │
│  QC-029: Apply Codes to Text ─────────────────────── [In Progress]  │
│  ├── Researcher: select, apply, remove coding ✓                     │
│  └── Agent: apply, list, remove segments                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
TIER 3: SPECIALIZED CODING (Image/AV)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-030: Apply Codes to Images                                      │
│  ├── Researcher: draw region, apply code                            │
│  └── Agent: detect regions, apply codes                             │
│                                                                     │
│  QC-031: Apply Codes to Audio/Video                                 │
│  ├── Researcher: mark time range, apply code                        │
│  └── Agent: transcribe, apply codes                                 │
│                                                                     │
│  QC-032: Auto-Code ──────────────────────────────── [In Progress]   │
│  └── 5/7 subtasks Done ✓                                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
TIER 4: ANALYSIS & REPORTING (Needs coded data)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-033: Search and Find                                            │
│  QC-035: Generate Reports                                           │
│  QC-044: Visualizations                                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
TIER 5: COLLABORATION & AI (Needs everything)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-036: Collaborate                                                │
│  QC-037: Chat with Agent ──────────────── (Consummate feature)      │
└─────────────────────────────────────────────────────────────────────┘

PARALLEL TRACK: AUXILIARY FEATURES (Can start after QC-026)
┌─────────────────────────────────────────────────────────────────────┐
│  QC-034: Manage Cases                                               │
│  QC-038: Settings and Preferences                                   │
│  QC-039: Import/Export Formats                                      │
│  QC-040: Data Privacy                                               │
│  QC-041: References and Bibliography                                │
│  QC-042: Apply Codes to PDF                                         │
│  QC-043: Journals and Memos                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Parallel Development: Researcher + Agent

Every feature has both Researcher and Agent acceptance criteria. They can be developed in parallel:

```
┌─────────────────────────────────────────────────────────────────────┐
│  EACH FEATURE = RESEARCHER AC + AGENT AC                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Example: QC-028 Manage Codes                                       │
│  ├── Researcher: create, edit, merge codes (UI)                     │
│  └── Agent: list, suggest, create codes (MCP)                       │
│                                                                     │
│  Both share same domain layer - develop in parallel!                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Current Status Summary

| Status | Count | Features |
|--------|-------|----------|
| ✓ Done/In Progress | 3 | QC-028, QC-029, QC-032 |
| Blocked | 2 | QC-030, QC-031 |
| To Do | 15 | QC-026, 027, 033-044 |

## Current Agent Capability Status

| Feature | Agent Capability | Status |
|---------|------------------|--------|
| QC-028 | List codes | ✅ Working |
| QC-028 | Get code details | ✅ Working |
| QC-028 | Suggest codes | ✅ Done |
| QC-028 | **Create new code** | ❌ Missing |
| QC-027 | List sources | ✅ Working |
| QC-027 | Read source content | ✅ Working |
| QC-027 | **Add text source** | ❌ Missing |
| QC-029 | Apply codes to text | ✅ Working |
| QC-029 | List coded segments | ✅ Working |
| QC-029 | Navigate to segment | ✅ Working |
| QC-029 | **Remove coded segment** | ❌ Missing |

## Recommended Sequence

### Phase 1: Foundation
```
QC-026 (Project) → QC-027 (Sources) → QC-028/029 (Coding)
```

### Phase 2: Complete Text Coding
```
QC-028: Add "Agent can create code" capability
QC-027: Add "Agent can add source" capability
QC-029: Add "Agent can remove segment" capability
```

### Phase 3: Specialized Coding
```
QC-030 (Image Coding) - Researcher + Agent
QC-031 (AV Coding) - Researcher + Agent
```

### Phase 4: Analysis & Collaboration
```
QC-033 (Search) → QC-035 (Reports) → QC-036 (Collaborate) → QC-037 (Chat)
```
