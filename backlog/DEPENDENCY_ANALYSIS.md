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
│  ├── 6/8 subtasks Done ✓                                            │
│  └── Pending: Agent suggest/detect                                  │
│                                                                     │
│  QC-029: Apply Codes to Text ─────────────────────── [In Progress]  │
│  ├── Core workflow implemented ✓                                    │
│  └── Pending: Agent suggestions                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
TIER 3: SPECIALIZED CODING (Blocked by QC-045 ⚡)
┌─────────────────────────────────────────────────────────────────────┐
│  ⚡ QC-045: Complete Coding Context ⚡ ──────────── [CRITICAL]      │
│  ├── QC-045.01: Image Coding Controller ──┐                         │
│  ├── QC-045.02: Image Coding Screen ──────┼── blocks QC-030         │
│  ├── QC-045.03: AV Coding Controller ─────┤                         │
│  ├── QC-045.04: AV Coding Screen ─────────┼── blocks QC-031         │
│  └── QC-045.05: MCP Tool Adapters ────────┴── blocks ALL agent ops  │
│                                                                     │
│  QC-030: Apply Codes to Images ───────── [Blocked by QC-045.01/02]  │
│  QC-031: Apply Codes to Audio/Video ──── [Blocked by QC-045.03/04]  │
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

PARALLEL TRACK: (Can start after QC-026)
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

## Cross-Feature Dependency Graph

```
                              ┌──────────────┐
                              │   QC-026     │
                              │   Project    │
                              └──────┬───────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
    ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
    │   QC-027     │          │   QC-028     │          │  PARALLEL    │
    │   Sources    │          │    Codes     │          │  QC-038,43   │
    │              │          │   [75% ✓]    │          │  Settings    │
    └──────┬───────┘          └──────┬───────┘          └──────────────┘
           │                         │
           └────────────┬────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   QC-029     │
                 │  Text Coding │
                 │   [80% ✓]    │
                 └──────┬───────┘
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
      ▼                 ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   QC-032     │ │   QC-042     │ │   QC-039     │
│  Auto-Code   │ │  PDF Coding  │ │   Export     │
│   [70% ✓]    │ │              │ │              │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       │         ⚡⚡⚡ CRITICAL BLOCKER ⚡⚡⚡
       │         ┌──────────────────────────────┐
       │         │         QC-045               │
       │         │   Complete Coding Context    │
       │         │                              │
       │         │  ┌────────┐    ┌────────┐   │
       │         │  │045.01  │    │045.03  │   │
       │         │  │Img Ctl │    │AV Ctl  │   │
       │         │  └───┬────┘    └───┬────┘   │
       │         │      │             │        │
       │         │  ┌───┴────┐    ┌───┴────┐   │
       │         │  │045.02  │    │045.04  │   │
       │         │  │Img Scr │    │AV Scr  │   │
       │         │  └────────┘    └────────┘   │
       │         │                              │
       │         │  ┌────────────────────────┐ │
       │         │  │       045.05           │ │
       │         │  │   MCP Tool Adapters    │ │
       │         │  └────────────────────────┘ │
       │         └──────────────┬───────────────┘
       │                        │
       │         ┌──────────────┴──────────────┐
       │         │                             │
       │         ▼                             ▼
       │  ┌──────────────┐              ┌──────────────┐
       │  │   QC-030     │              │   QC-031     │
       │  │ Image Coding │              │  AV Coding   │
       │  │  [BLOCKED]   │              │  [BLOCKED]   │
       │  └──────┬───────┘              └──────┬───────┘
       │         │                             │
       └─────────┼─────────────────────────────┘
                 │
                 ▼
          ┌──────────────┐
          │   QC-033     │
          │   Search     │
          └──────┬───────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ QC-035   │ │ QC-034   │ │ QC-044   │
│ Reports  │ │  Cases   │ │   Viz    │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
           ┌──────────────┐
           │   QC-036     │
           │ Collaborate  │
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │   QC-037     │
           │  Chat Agent  │
           │   (FINAL)    │
           └──────────────┘
```

## Current Status Summary

| Status | Count | Features |
|--------|-------|----------|
| ✓ Done/In Progress | 3 | QC-028, QC-029, QC-032 |
| ⚡ Critical Blocker | 1 | QC-045 (blocks 2 features + all agent) |
| Blocked | 2 | QC-030, QC-031 |
| To Do | 14 | QC-026, 027, 033-044 |

## Recommended Sequence

### Phase 1: Foundation (Current Focus)
```
QC-026 → QC-027 → Stabilize QC-028/029
```

### Phase 2: Unlock Specialized Coding ⚡
```
QC-045.01 (Image Controller)
QC-045.02 (Image Screen)
    └── UNBLOCKS → QC-030 (Image Coding)

QC-045.03 (AV Controller)
QC-045.04 (AV Screen)
    └── UNBLOCKS → QC-031 (AV Coding)

QC-045.05 (MCP Adapters)
    └── UNBLOCKS → All agent coding operations
```

### Phase 3: Analysis Features
```
QC-033 (Search) → QC-035 (Reports) → QC-044 (Viz)
```

### Phase 4: Collaboration & AI
```
QC-036 (Collaborate) → QC-037 (Chat Agent)
```

## Key Insight

**QC-045 is the critical bottleneck.** Until it's complete:
- QC-030 (Image Coding) cannot be implemented
- QC-031 (AV Coding) cannot be implemented
- Agent cannot perform any coding operations
- 7+ downstream features remain blocked

The domain layer is ready (ImageSegment, AVSegment, TimeRange entities exist).
What's needed: Application controllers + Presentation screens + MCP adapters.
