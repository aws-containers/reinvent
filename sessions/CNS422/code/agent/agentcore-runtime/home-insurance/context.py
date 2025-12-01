from contextvars import ContextVar
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.multiagent.a2a import A2AServer
from typing import Optional, Dict


class AgentContext:
    """Context Manager for Agent - uses class-level storage for persistence across requests."""

    # Class-level storage for persistent data across requests
    _sessions: Dict[str, Dict] = {}

    # ContextVars for request-scoped data
    _current_session_id: ContextVar[Optional[str]] = ContextVar("current_session_id", default=None)
    _agent_identity_token: ContextVar[Optional[str]] = ContextVar("agent_identity_token", default=None)

    @classmethod
    def get_session_id(cls) -> Optional[str]:
        """Get current session ID from request context."""
        try:
            return cls._current_session_id.get()
        except LookupError:
            return None

    @classmethod
    def set_session_id(cls, session_id: str) -> None:
        """Set current session ID and initialize session storage if needed."""
        cls._current_session_id.set(session_id)
        if session_id not in cls._sessions:
            cls._sessions[session_id] = {
                "gateway_client": None,
                "agent": None,
                "a2a_server": None,
                "gateway_url": None
            }

    @classmethod
    def get_agent_identity_token(cls) -> Optional[str]:
        """Get agent identity token from context."""
        try:
            return cls._agent_identity_token.get()
        except LookupError:
            return None

    @classmethod
    def set_agent_identity_token(cls, token: str) -> None:
        """Set agent identity token in context."""
        cls._agent_identity_token.set(token)

    @classmethod
    def get_gateway_url(cls) -> Optional[str]:
        """Get gateway URL for current session."""
        session_id = cls.get_session_id()
        if session_id and session_id in cls._sessions:
            return cls._sessions[session_id].get("gateway_url")
        return None

    @classmethod
    def set_gateway_url(cls, url: str) -> None:
        """Set gateway URL for current session."""
        session_id = cls.get_session_id()
        if session_id:
            if session_id not in cls._sessions:
                cls._sessions[session_id] = {}
            cls._sessions[session_id]["gateway_url"] = url

    @classmethod
    def get_agent(cls) -> Optional[Agent]:
        """Get agent for current session."""
        session_id = cls.get_session_id()
        if session_id and session_id in cls._sessions:
            return cls._sessions[session_id].get("agent")
        return None

    @classmethod
    def set_agent(cls, agent: Agent) -> None:
        """Set agent for current session."""
        session_id = cls.get_session_id()
        if session_id:
            if session_id not in cls._sessions:
                cls._sessions[session_id] = {}
            cls._sessions[session_id]["agent"] = agent

    @classmethod
    def get_gateway_client(cls) -> Optional[MCPClient]:
        """Get gateway client for current session."""
        session_id = cls.get_session_id()
        if session_id and session_id in cls._sessions:
            return cls._sessions[session_id].get("gateway_client")
        return None

    @classmethod
    def set_gateway_client(cls, client: MCPClient) -> None:
        """Set gateway client for current session."""
        session_id = cls.get_session_id()
        if session_id:
            if session_id not in cls._sessions:
                cls._sessions[session_id] = {}
            cls._sessions[session_id]["gateway_client"] = client

    @classmethod
    def get_a2a_server(cls) -> Optional[A2AServer]:
        """Get A2A server for current session."""
        session_id = cls.get_session_id()
        if session_id and session_id in cls._sessions:
            return cls._sessions[session_id].get("a2a_server")
        return None

    @classmethod
    def set_a2a_server(cls, server: A2AServer) -> None:
        """Set A2A server for current session."""
        session_id = cls.get_session_id()
        if session_id:
            if session_id not in cls._sessions:
                cls._sessions[session_id] = {}
            cls._sessions[session_id]["a2a_server"] = server

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        """Clear session data for cleanup."""
        if session_id in cls._sessions:
            del cls._sessions[session_id]
