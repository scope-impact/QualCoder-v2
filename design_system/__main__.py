"""
Run the Design System Storybook

Usage:
    cd _template
    uv run python -m design_system

    # Or from project root:
    cd QualCoder-v2
    python -m design_system
"""

from .storybook import main

if __name__ == "__main__":
    main()
