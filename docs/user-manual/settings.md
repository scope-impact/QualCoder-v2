# Settings and Preferences

Configure QualCoder to match your workflow and preferences.

## Opening Settings

Access settings from the menu bar:

1. Click **Settings** in the menu bar (or press `Cmd+,` on macOS)
2. The Settings dialog opens with a sidebar for navigation

## Appearance

### Theme

Choose between light and dark themes:

1. Go to **Appearance** in the sidebar
2. Click **Light** or **Dark** theme button
3. The UI updates immediately

> **Tip: Eye Strain**
>
> Use dark theme in low-light environments to reduce eye strain during extended coding sessions.

### Font Size

Adjust the application font size:

1. In **Appearance**, find the Font Size slider
2. Drag the slider between 10px and 24px
3. The preview updates as you adjust

### Font Family

Choose your preferred font:

1. In **Appearance**, find the Font Family dropdown
2. Select from available fonts (Inter, Roboto, System Default)
3. The change applies immediately

## Language

Select your preferred application language:

1. Go to **Language** in the sidebar
2. Choose from available languages:
   - English
   - Spanish
   - German
   - French
   - Portuguese
3. Some changes may require restart

> **Note: Translation Coverage**
>
> Not all languages have complete translations. Missing translations fall back to English.

## Backup Settings

Configure automatic project backups:

### Enable Backups

1. Go to **Backup** in the sidebar
2. Check **Enable automatic backups**

### Backup Interval

Set how often backups are created:

1. Enable backups first
2. Set the interval (in minutes) using the spinbox
3. Default is 30 minutes

> **Warning: Backup Location**
>
> Backups are stored alongside your project file. Ensure you have sufficient disk space.

## AV Coding Settings

Configure settings for audio/video coding:

### Timestamp Format

Choose how timestamps are displayed:

1. Go to **AV Coding** in the sidebar
2. Select a timestamp format:
   - **HH:MM:SS** - Hours, minutes, seconds (default)
   - **MM:SS** - Minutes and seconds only
   - **SS.ms** - Seconds with milliseconds

### Speaker Format

Customize how speaker names appear in transcripts:

1. In **AV Coding**, find Speaker Format
2. Enter your preferred format using `{n}` as a placeholder
3. Examples:
   - `Speaker {n}` → Speaker 1, Speaker 2
   - `P{n}` → P1, P2
   - `Interviewee {n}` → Interviewee 1, Interviewee 2

The preview shows how speaker names will appear.

## Saving Settings

Settings are saved automatically as you change them. There's no need to click Save.

- **OK** - Closes the dialog
- **Cancel** - Closes the dialog (changes are already saved)

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Settings | `Cmd+,` (macOS) / `Ctrl+,` (Windows/Linux) |

## Next Steps

- [Start coding your text](coding.md)
- [Manage your codes](codes.md)
- [Import sources](sources.md)
