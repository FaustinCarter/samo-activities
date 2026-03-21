"""In-memory session manager mapping session IDs to per-user API clients."""

import logging
import secrets
import time

from app import config
from app.client import ActiveNetClient

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages a pool of :class:`ActiveNetClient` instances, one per visitor.

    Each session is identified by a cryptographically random token stored in
    the visitor's browser as an HTTP-only cookie.  Anonymous visitors get a
    bootstrapped (but unauthenticated) client; logging in upgrades that same
    client in-place.  Logging out destroys the session entirely.

    All state is held in memory — sessions do not survive a server restart.

    **Eviction policy**: Sessions that have not been accessed within
    ``session_ttl_seconds`` (default 1 hour) are lazily evicted.  If the
    session count exceeds ``session_max_count``, the oldest sessions are
    evicted first regardless of TTL.
    """

    def __init__(
        self,
        ttl_seconds: int | None = None,
        max_count: int | None = None,
    ) -> None:
        self._sessions: dict[str, tuple[ActiveNetClient, float]] = {}
        self._ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else config.settings.session_ttl_seconds
        )
        self._max_count = (
            max_count if max_count is not None else config.settings.session_max_count
        )

    async def create_session(self) -> tuple[str, ActiveNetClient]:
        """Bootstrap a new anonymous session and return ``(session_id, client)``."""
        self._evict_expired()

        session_id = secrets.token_urlsafe(32)
        client = ActiveNetClient()
        await client.bootstrap()
        self._sessions[session_id] = (client, time.monotonic())

        self._evict_overflow()

        logger.info("Created anonymous session %s…", session_id[:8])
        return session_id, client

    def get_client(self, session_id: str) -> ActiveNetClient | None:
        """Look up the client for *session_id*, or ``None`` if not found.

        Updates the session's last-accessed timestamp on hit.  Returns
        ``None`` (and removes the entry) if the session has expired.
        """
        entry = self._sessions.get(session_id)
        if entry is None:
            return None

        client, last_accessed = entry
        if time.monotonic() - last_accessed > self._ttl:
            # Session expired — clean it up.
            self._remove_session(session_id, client)
            return None

        # Touch — update last-accessed time.
        self._sessions[session_id] = (client, time.monotonic())
        return client

    def destroy_session(self, session_id: str) -> None:
        """Remove a session and clear its client state."""
        entry = self._sessions.pop(session_id, None)
        if entry is not None:
            client, _ = entry
            client.logout()
            logger.info("Destroyed session %s…", session_id[:8])

    @property
    def active_count(self) -> int:
        """Return the number of sessions currently stored."""
        return len(self._sessions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _remove_session(self, session_id: str, client: ActiveNetClient) -> None:
        """Pop a session and log out its client."""
        self._sessions.pop(session_id, None)
        client.logout()
        logger.info("Evicted expired session %s…", session_id[:8])

    def _evict_expired(self) -> None:
        """Remove sessions older than the TTL."""
        now = time.monotonic()
        expired = [
            sid
            for sid, (_, last_accessed) in self._sessions.items()
            if now - last_accessed > self._ttl
        ]
        for sid in expired:
            client, _ = self._sessions.pop(sid)
            client.logout()
            logger.info("Evicted expired session %s…", sid[:8])

    def _evict_overflow(self) -> None:
        """If over capacity, evict the oldest sessions first."""
        overflow = len(self._sessions) - self._max_count
        if overflow > 0:
            by_age = sorted(self._sessions.items(), key=lambda item: item[1][1])
            for sid, (client, _) in by_age[:overflow]:
                self._sessions.pop(sid, None)
                client.logout()
                logger.info("Evicted over-capacity session %s…", sid[:8])
