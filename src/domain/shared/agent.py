"""
Agent foundation types - TrustLevel and AgentSession

Shared across all bounded contexts for agent-aware operations.
These types establish the trust and identity model for AI agent interactions.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class TrustLevel(Enum):
    """
    Permission level required for agent tool execution.

    Determines how much autonomy an AI agent has when performing operations:
    - AUTONOMOUS: Execute immediately without user notification
    - NOTIFY: Execute and inform the user afterward
    - SUGGEST: Queue for user approval before execution
    - REQUIRE: Block until user explicitly approves
    """
    AUTONOMOUS = "auto"
    NOTIFY = "notify"
    SUGGEST = "suggest"
    REQUIRE = "require"


@dataclass(frozen=True)
class AgentSession:
    """
    Base type representing an AI agent session.

    Tracks the identity and trust level of a connected AI client.
    Used across all contexts to attribute actions and enforce permissions.

    Attributes:
        session_id: Unique identifier for this session
        agent_id: Identifier for the agent type (e.g., "claude-code")
        trust_level: Permission level for this session
        created_at: When the session was established
        metadata: Optional additional session information
    """
    session_id: str
    agent_id: str
    trust_level: TrustLevel
    created_at: datetime
    metadata: Optional[dict[str, Any]] = None
