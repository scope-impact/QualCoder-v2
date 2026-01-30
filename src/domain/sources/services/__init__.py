"""
Sources Domain Services

Pure domain services for the Sources bounded context.
"""

from src.domain.sources.services.speaker_detector import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

__all__ = [
    "Speaker",
    "SpeakerDetector",
    "SpeakerSegment",
]
