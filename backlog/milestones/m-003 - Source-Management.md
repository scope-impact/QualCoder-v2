---
id: M-003
title: Source Management
status: To Do
created_date: '2026-01-29'
dependencies: [M-002]
---

## Description

Implement the Source Management bounded context end-to-end - importing, organizing, and managing research data files.

**Agent-First:** AI can import files, list sources, and read content for analysis.

## Goals

- Support text, image, audio, video, PDF sources
- File organization with folders
- Text extraction and transcription
- Source preview and metadata
- MCP tools for source operations

## Tasks

| ID | Task | Layer | Status |
|----|------|-------|--------|
| QC-008 | Source Domain | Domain | To Do |
| QC-009 | Source Infrastructure | Infrastructure | To Do |
| QC-010 | Source Application | Application | To Do |
| QC-011 | Source Presentation | Presentation | To Do |

## Success Criteria

- [ ] Source and Folder entities
- [ ] Import from filesystem
- [ ] Text extraction from PDF
- [ ] File manager screen functional
- [ ] MCP tools: list_sources, read_source, import_file
- [ ] Agent can read source content for coding suggestions
