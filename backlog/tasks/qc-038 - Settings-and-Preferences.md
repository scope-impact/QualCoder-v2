---
id: QC-038
title: Settings and Preferences
status: Done
assignee: []
created_date: '2026-01-30 21:14'
updated_date: '2026-02-04 06:19'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable researchers to customize the application appearance, behavior, and backup settings.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Researcher can change UI theme (dark, light, colors)
- [x] #2 Researcher can configure font size and family
- [x] #3 Researcher can select application language
- [x] #4 Researcher can configure automatic backups
- [x] #5 Researcher can set timestamp format for AV coding
- [x] #6 Researcher can configure speaker name format
- [ ] #7 Agent can read current settings for context
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Settings feature fully implemented with DDD architecture:

**Domain Layer** (`src/domain/settings/`):
- Entities: ThemePreference, FontPreference, LanguagePreference, BackupConfig, AVCodingConfig, UserSettings
- Events: ThemeChanged, FontChanged, LanguageChanged, BackupConfigChanged, AVCodingConfigChanged
- Derivers: Pure validation functions for each setting type
- Invariants: Valid values and validators

**Infrastructure Layer** (`src/infrastructure/settings/`):
- UserSettingsRepository: JSON file persistence with platform-specific paths

**Application Layer** (`src/application/settings/`):
- SettingsControllerImpl: 5-step controller pattern
- Commands: ChangeTheme, ChangeFont, ChangeLanguage, ChangeBackupConfig, ChangeAVCodingConfig

**Presentation Layer**:
- SettingsDialog: Tabbed UI (Appearance, Language, Backup, AV Coding)
- SettingsViewModel: Transforms domain to DTOs
- AppShell integration: Settings button with gear icon in menu bar

**Tests**:
- 66 unit tests (derivers, repository, controller)
- 17 E2E tests (dialog, persistence, round-trip)
- 6 integration tests (AppShell settings button)
<!-- SECTION:NOTES:END -->
