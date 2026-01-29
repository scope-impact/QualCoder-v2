#!/usr/bin/env python3
"""
Run the Design System Storybook

Usage (from QualCoder-v2 root):
    cd _template
    uv run python ../design_system/run_storybook.py

Or if PyQt6 is installed globally:
    python design_system/run_storybook.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from design_system.storybook import main

if __name__ == "__main__":
    main()
