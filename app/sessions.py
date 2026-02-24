"""In-memory session manager mapping session IDs to per-user API clients."""

import logging
import secrets

from app.client import ActiveNetClient

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages a pool of :class:`ActiveNetClient` instances, one per visitor.

    Each session is identified by a cryptographically random token stored in
    the visitor's browser as an HTTP-only cookie.  Anonymous visitors get a
    bootstrapped (but unauthenticated) client; logging in upgrades that same
    client in-place.  Logging out destroys the session entirely.

    All state is held in memory — sessions do not survive a server restart.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ActiveNetClient] = {}

    async def create_session(self) -> tuple[str, ActiveNetClient]:
        """Bootstrap a new anonymous session and return ``(session_id, client)``."""
        session_id = secrets.token_urlsafe(32)
        client = ActiveNetClient()
        await client.bootstrap()
        self._sessions[session_id] = client
        logger.info("Created anonymous session %s…", session_id[:8])
        return session_id, client

    def get_client(self, session_id: str) -> ActiveNetClient | None:
        """Look up the client for *session_id*, or ``None`` if not found."""
        return self._sessions.get(session_id)

    def destroy_session(self, session_id: str) -> None:
        """Remove a session and clear its client state."""
        client = self._sessions.pop(session_id, None)
        if client is not None:
            client.logout()
            logger.info("Destroyed session %s…", session_id[:8])
