---
id: QC-047
title: SQLite Database Version Control with Git
status: To Do
created_date: '2026-02-04'
labels: [infrastructure, projects, feature, P1]
dependencies: []
decision: decision-006
---

## Description

As a Researcher, I want my project database to be automatically version controlled so that every change is tracked and I can rollback mistakes without manual effort.

## Acceptance Criteria

- [ ] #1 I can initialize version control for my project
- [ ] #2 Every mutation (create code, apply segment, etc.) auto-commits
- [ ] #3 I can view the history of all changes
- [ ] #4 I can see what changed between two points in time
- [ ] #5 I can restore my project to a previous state
- [ ] #6 I can create branches for different analysis approaches
- [ ] #7 I can merge changes from different branches

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-047.01 | Git repository initialization | To Do |
| QC-047.02 | sqlite-diffable adapter | To Do |
| QC-047.03 | Git operations service | To Do |
| QC-047.04 | VersionControlListener with debounce | To Do |
| QC-047.05 | Restore snapshot command | To Do |
| QC-047.06 | Version history UI | To Do |
| QC-047.07 | Diff viewer dialog | To Do |
| QC-047.08 | MCP tools | To Do |
| QC-047.09 | User documentation | To Do |

## References

- [decision-006](../decisions/decision-006%20sqlite-version-control-sqlite-diffable.md) - Architecture decision record
