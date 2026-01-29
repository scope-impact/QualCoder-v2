"""Agent Context Layer - AI-first interface for external AI systems

Exposes QualCoder capabilities via:
- MCP Server (Claude Code)
- REST API (Generic AI clients)
- WebSocket (Real-time events)

Components:
- Protocol Adapters: MCP, REST, WebSocket, gRPC
- Session Manager: Track connected AI clients
- Capability Registry: Define available tools/resources
- Trust Layer: Enforce permission policies
- Event Broadcaster: Stream domain events to subscribers
"""
