---
id: QC-034
title: Manage Cases
status: In Progress
assignee: []
created_date: '2026-01-30 20:35'
updated_date: '2026-02-06 09:11'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable researchers and agents to organize data into cases (e.g., participants, sites) with attributes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Researcher can create cases
- [ ] #2 Researcher can link sources to cases
- [ ] #3 Researcher can add case attributes
- [ ] #4 Researcher can view all data for a case
- [ ] #5 Agent can list all cases
- [ ] #6 Agent can suggest case groupings
- [ ] #7 Agent can compare across cases
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Overall Status (2026-02-06): ~80% core implementation done**

Domain + Infra + Command Handlers: COMPLETE for all 7 subtasks
MCP Tools: 4 tools implemented (list, get, suggest_groupings, compare)
MCP Server: Case tools NOT exposed yet (same gap fixed for project tools today)

**Remaining work across all subtasks:**
1. Expose case tools in MCP server (quick win)
2. Add missing MCP tools: create_case, link_source, set_attribute, unlink_source, remove_case
3. Wire CaseManagerViewModel in main.py
4. Build UI dialogs (Create, Edit, Link, Attribute)
5. E2E tests with @allure.story decorators
6. Documentation (API + user manual)
7. compare_cases cross-context integration with coding
<!-- SECTION:NOTES:END -->
