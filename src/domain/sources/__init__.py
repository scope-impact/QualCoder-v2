"""
Source Management Context - Research data files and content

DEPRECATED: This module is a re-export for backward compatibility.
New code should import from src.contexts.sources.core
"""

from src.contexts.sources.core import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

__all__ = [
    "Speaker",
    "SpeakerDetector",
    "SpeakerSegment",
]
