"""Tests for session middleware, the get_api_client dependency, and auth routes."""

import respx
from httpx import Response

from app.config import settings
from app.sessions import SessionManager


class TestSessionMiddleware:
    """Tests that the session middleware sets cookies correctly."""

    @respx.mock
    def test_first_visit_sets_session_cookie(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """A visitor with no cookie gets a samo_session cookie on the response."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/", cookies={})

        assert response.status_code == 200
        assert "samo_session" in response.cookies

    @respx.mock
    def test_returning_visitor_keeps_session(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """A visitor who already has a valid session cookie does not get a new one."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        # First request — establishes the session.
        first = client.get("/")
        session_id = first.cookies["samo_session"]

        # Second request with the same cookie — should reuse the session.
        second = client.get("/", cookies={"samo_session": session_id})
        assert second.status_code == 200
        # No new Set-Cookie header when the session already exists.
        assert "samo_session" not in second.cookies

    @respx.mock
    def test_invalid_session_cookie_creates_new_session(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """An unrecognised session ID causes a fresh session to be created."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/", cookies={"samo_session": "bogus-token"})

        assert response.status_code == 200
        # A new cookie should be set to replace the bogus one.
        assert "samo_session" in response.cookies
        assert response.cookies["samo_session"] != "bogus-token"

    @respx.mock
    def test_cookie_set_on_template_response(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """Cookie is delivered even when the route returns a TemplateResponse."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "samo_session" in response.cookies


class TestLoginRoutes:
    """Tests for the /login GET and POST routes."""

    @respx.mock
    def test_login_page_renders(self, client):
        """GET /login renders the login form for unauthenticated users."""
        response = client.get("/login")

        assert response.status_code == 200
        assert "Sign In" in response.text
        assert '<form method="post"' in response.text

    @respx.mock
    def test_login_page_sets_session_cookie(self, client):
        """GET /login also sets the session cookie (via middleware)."""
        response = client.get("/login")

        assert response.status_code == 200
        assert "samo_session" in response.cookies

    @respx.mock
    def test_login_page_redirects_when_authenticated(self, authenticated_client):
        """GET /login redirects to / if the user is already logged in."""
        response = authenticated_client.get(
            "/login",
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @respx.mock
    def test_login_success_redirects_home(self, client):
        """POST /login redirects to / on successful authentication."""
        # Get a session first.
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        # Mock the upstream login API call.
        respx.post(f"{settings.base_url}/user/signin").mock(
            return_value=Response(
                200,
                json={
                    "headers": {
                        "response_code": "0000",
                        "response_message": "Success",
                    },
                    "body": {
                        "result": {
                            "access_token": "at-123",
                            "refresh_token": "rt-456",
                            "customer": {"name": "Test User"},
                        }
                    },
                },
            )
        )

        response = client.post(
            "/login",
            data={"username": "test@example.com", "password": "secret"},
            cookies={"samo_session": session_id},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/"

        # Verify the client is now authenticated.
        api_client = client.app.state.session_manager.get_client(session_id)
        assert api_client.is_authenticated

    @respx.mock
    def test_login_failure_shows_error(self, client):
        """POST /login re-renders the form with an error on API failure."""
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        respx.post(f"{settings.base_url}/user/signin").mock(
            return_value=Response(
                200,
                json={
                    "headers": {
                        "response_code": "9999",
                        "response_message": "Invalid credentials",
                    },
                    "body": {},
                },
            )
        )

        response = client.post(
            "/login",
            data={"username": "bad@example.com", "password": "wrong"},
            cookies={"samo_session": session_id},
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.text

    @respx.mock
    def test_login_unexpected_error_shows_generic_message(self, client):
        """POST /login shows a generic error on unexpected exceptions."""
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        # Simulate a network-level failure.
        respx.post(f"{settings.base_url}/user/signin").mock(
            side_effect=RuntimeError("connection reset")
        )

        response = client.post(
            "/login",
            data={"username": "test@example.com", "password": "secret"},
            cookies={"samo_session": session_id},
        )

        assert response.status_code == 500
        assert "Login failed" in response.text


class TestLogoutRoute:
    """Tests for the GET /logout route."""

    @respx.mock
    def test_logout_redirects_home(self, client):
        """GET /logout redirects to /."""
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        response = client.get(
            "/logout",
            cookies={"samo_session": session_id},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @respx.mock
    def test_logout_destroys_session(self, client):
        """GET /logout removes the session from the manager."""
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        session_manager = client.app.state.session_manager
        assert session_manager.get_client(session_id) is not None

        client.get(
            "/logout",
            cookies={"samo_session": session_id},
            follow_redirects=False,
        )

        assert session_manager.get_client(session_id) is None

    @respx.mock
    def test_logout_deletes_cookie(self, client):
        """GET /logout sends a Set-Cookie to clear the browser cookie."""
        first = client.get("/login")
        session_id = first.cookies["samo_session"]

        response = client.get(
            "/logout",
            cookies={"samo_session": session_id},
            follow_redirects=False,
        )

        # The logout route explicitly deletes the cookie; the value should be
        # empty or the max-age should be 0 in the Set-Cookie header.
        set_cookie = response.headers.get("set-cookie", "")
        assert "samo_session" in set_cookie

    @respx.mock
    def test_logout_without_session_still_redirects(self, client):
        """GET /logout works even if there is no session cookie."""
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"


class TestSessionManager:
    """Unit tests for the SessionManager class."""

    async def test_create_session_returns_id_and_client(self):
        """create_session returns a (session_id, client) tuple."""
        manager = SessionManager()
        session_id, client = await manager.create_session()

        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert client is not None

    async def test_get_client_returns_none_for_unknown_id(self):
        """get_client returns None for an unrecognised session ID."""
        manager = SessionManager()

        assert manager.get_client("nonexistent") is None

    async def test_get_client_returns_stored_client(self):
        """get_client returns the client that was created."""
        manager = SessionManager()
        session_id, client = await manager.create_session()

        assert manager.get_client(session_id) is client

    async def test_destroy_session_removes_client(self):
        """destroy_session removes the session so get_client returns None."""
        manager = SessionManager()
        session_id, _ = await manager.create_session()

        manager.destroy_session(session_id)

        assert manager.get_client(session_id) is None

    async def test_destroy_session_clears_client_state(self):
        """destroy_session calls logout on the client, clearing its tokens."""
        manager = SessionManager()
        session_id, client = await manager.create_session()
        client.access_token = "fake-token"

        manager.destroy_session(session_id)

        assert client.access_token is None

    def test_destroy_nonexistent_session_is_noop(self):
        """destroy_session does not raise for an unknown session ID."""
        manager = SessionManager()
        manager.destroy_session("nonexistent")  # should not raise

    async def test_active_count_tracks_sessions(self):
        """active_count reflects the number of live sessions."""
        manager = SessionManager()
        assert manager.active_count == 0

        sid1, _ = await manager.create_session()
        assert manager.active_count == 1

        await manager.create_session()
        assert manager.active_count == 2

        manager.destroy_session(sid1)
        assert manager.active_count == 1


class TestSessionEviction:
    """Tests for session TTL expiration and max-count eviction."""

    async def test_expired_session_returns_none(self):
        """get_client returns None for a session that has exceeded the TTL."""
        manager = SessionManager(ttl_seconds=0)  # expire immediately
        session_id, _ = await manager.create_session()

        # Session should be expired on the next get_client call.
        assert manager.get_client(session_id) is None
        assert manager.active_count == 0

    async def test_expired_session_clears_client_state(self):
        """Evicted expired sessions have their client state cleared."""
        manager = SessionManager(ttl_seconds=0)
        _, client = await manager.create_session()
        client.access_token = "fake-token"

        # Trigger eviction by creating another session.
        await manager.create_session()

        assert client.access_token is None

    async def test_max_count_evicts_oldest(self):
        """When max_count is exceeded, the oldest session is evicted."""
        manager = SessionManager(max_count=2)
        sid1, client1 = await manager.create_session()
        sid2, _ = await manager.create_session()

        # Touch sid2 so it's newer, then create a 3rd which should evict sid1.
        manager.get_client(sid2)
        sid3, _ = await manager.create_session()

        assert manager.active_count == 2
        assert manager.get_client(sid1) is None  # evicted (oldest)
        assert client1.access_token is None  # logout was called
        assert manager.get_client(sid3) is not None  # newest kept

    async def test_get_client_touches_session(self):
        """Accessing a session updates its last-accessed time."""
        manager = SessionManager(ttl_seconds=1000)
        session_id, _ = await manager.create_session()

        # Access should succeed and keep the session alive.
        client = manager.get_client(session_id)
        assert client is not None

        # Still alive on subsequent access.
        assert manager.get_client(session_id) is not None
