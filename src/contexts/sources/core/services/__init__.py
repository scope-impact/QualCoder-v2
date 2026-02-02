"""
Sources Domain Services

Pure domain services for the Sources bounded context.
"""

from src.contexts.sources.core.services.speaker_detector import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

__all__ = [
    "Speaker",
    "SpeakerDetector",
    "SpeakerSegment",
]
