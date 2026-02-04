# Getting Started

This guide walks you through installing QualCoder v2 and creating your first project.

## Installation

### macOS / Linux

```bash
# Clone the repository
git clone https://github.com/scope-impact/qualcoder-v2
cd qualcoder-v2

# Install dependencies
uv sync

# Run the application
uv run python src/main.py
```

### Windows

```powershell
# Clone the repository
git clone https://github.com/scope-impact/qualcoder-v2
cd qualcoder-v2

# Install dependencies
uv sync

# Run the application
uv run python src/main.py
```

> **Tip: Using uv**
>
> We recommend using [uv](https://github.com/astral-sh/uv) for Python package management. It's fast and handles virtual environments automatically.

## Creating a Project

A project is a container for all your research data: sources, codes, and annotations.

### Step 1: Launch QualCoder

```bash
uv run python src/main.py
```

### Step 2: Create New Project

1. Click **File > New Project** from the menu
2. Enter a descriptive project name
3. Choose a save location
4. Click **Create**

> **Info: Project Files**
>
> QualCoder saves projects as `.qda` files (SQLite databases). All your data is stored in this single file, making it easy to backup and share.

### Step 3: Open an Existing Project

1. Click **File > Open Project**
2. Navigate to your `.qda` file
3. Click **Open**

## Project Structure

Once your project is open, you'll see the main application shell with:

- **Menu Bar** - File, Edit, View, AI, Help menus
- **Navigation** - Switch between screens (Files, Coding, Cases, etc.)
- **Content Area** - The main workspace for the current screen
- **Status Bar** - Current project name and status indicators

## Next Steps

Now that you have a project, you can:

1. [Import source documents](sources.md) to analyze
2. [Create codes](codes.md) for your coding scheme
3. [Start coding](coding.md) your data
