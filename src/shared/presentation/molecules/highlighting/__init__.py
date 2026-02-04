"""
Highlighting molecules.

Provides reusable highlighting utilities:
- OverlapDetector: Detects and merges overlapping text ranges
"""

from .overlap_detector import OverlapDetector

__all__ = ["OverlapDetector"]
