"""
Sources Domain Services

DEPRECATED: This module is a re-export for backward compatibility.
New code should import from src.contexts.sources.core.services
"""

from src.contexts.sources.core.services import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

__all__ = [
    "Speaker",
    "SpeakerDetector",
    "SpeakerSegment",
]
