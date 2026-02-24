import json
import logging
import re

import httpx

from app import config

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when the upstream API returns a non-success response code."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API Error {code}: {message}")


class BootstrapError(Exception):
    """Raised when the session bootstrap (CSRF token extraction) fails."""


class ActiveNetClient:
    """HTTP client wrapper for the ActiveNet REST API.

    Each instance represents one user session.  An anonymous session is created
    by calling :meth:`bootstrap` which fetches the sign-in page to obtain a
    CSRF token and initial session cookies.  Calling :meth:`login` upgrades the
    session to an authenticated one.  Calling :meth:`logout` clears all session
    state.

    **Password handling**: The ``login`` method accepts a plaintext password as
    a function parameter, passes it to the upstream API in a single HTTPS POST
    request, and never stores it on the instance.  Once ``login`` returns, the
    password variable is out of scope and eligible for garbage collection.
    """

    def __init__(self) -> None:
        self.base_url: str = config.settings.base_url
        self.session_cookie: str = ""
        self.csrf_token: str = ""
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user_info: dict | None = None

        base_site_url = config.settings.base_site_url
        self._origin = base_site_url
        self._referer = (
            f"{base_site_url}/activity/search"
            "?onlineSiteId=0&activity_select_param=2&viewMode=list"
        )

    @property
    def is_authenticated(self) -> bool:
        """Whether this client has a logged-in user session."""
        return self.access_token is not None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def bootstrap(self) -> None:
        """Fetch the sign-in page to obtain a CSRF token and session cookies.

        The ActiveNet sign-in page embeds a CSRF token in an inline script tag
        as ``window.__csrfToken = "<uuid>"``.  This method performs a GET
        request (following redirects) to that page, extracts the token via
        regex, and captures all cookies set by the response chain.
        """
        signin_url = (
            f"{config.settings.base_site_url}/signin"
            "?onlineSiteId=0&from_original_cui=true"
        )
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(signin_url)
            response.raise_for_status()

            # Extract CSRF token from the HTML
            match = re.search(r'__csrfToken\s*=\s*"([^"]+)"', response.text)
            if not match:
                raise BootstrapError("Could not extract __csrfToken from sign-in page")
            self.csrf_token = match.group(1)

            # Collect all cookies from the cookie jar (accumulated across
            # redirects) into a single Cookie header string.
            self.session_cookie = _serialize_cookie_jar(client.cookies)

        logger.info("Bootstrap complete — CSRF token acquired")

    async def login(self, username: str, password: str) -> dict:
        """Authenticate with the ActiveNet API.

        Sends the credentials to ``POST /rest/user/signin`` and captures the
        returned session cookies, access token, and refresh token.

        **The *password* parameter is never stored on this instance.**  It
        exists only as a local variable for the duration of this call and is
        passed to the upstream API in a single HTTPS POST body.

        Returns the parsed response ``body`` dict on success.

        Raises :class:`APIError` if the upstream API rejects the credentials.
        """
        url = f"{self.base_url}/user/signin"
        headers = self._get_headers("POST")
        params = self._get_params()

        # Build the request body — password is used here and nowhere else.
        body = {
            "login_name": username,
            "password": password,
            "signin_source_app": "0",
            "custom_amount": "False",
            "from_original_cui": "true",
            "onlineSiteId": "0",
            "override_partial_error": "False",
            "params": None,
            "ak_properties": None,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, json=body)

        # After this point ``password`` is no longer referenced — the local
        # variable will be garbage-collected.

        response.raise_for_status()
        data = response.json()
        self._check_response(data)

        # Update session cookies from Set-Cookie response headers.
        self._update_cookies_from_response(response)

        # Store tokens and user info (no password).
        result = data.get("body", {}).get("result", {})
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        self.user_info = result.get("customer")

        logger.info("Login successful for %s", username)
        return data.get("body", {})

    def logout(self) -> None:
        """Clear all session state."""
        self.session_cookie = ""
        self.csrf_token = ""
        self.access_token = None
        self.refresh_token = None
        self.user_info = None

    # ------------------------------------------------------------------
    # API request methods
    # ------------------------------------------------------------------

    def _get_headers(
        self,
        method: str = "GET",
        page_info: dict | None = None,
    ) -> dict[str, str]:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "Origin": self._origin,
            "Referer": self._referer,
        }
        if self.session_cookie:
            headers["Cookie"] = self.session_cookie

        if method == "GET":
            headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
        elif method == "POST":
            headers["Content-Type"] = "application/json;charset=utf-8"
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            # The API controls pagination via a page_info request header (not a
            # query param), matching exactly what the browser sends.
            pi = page_info or {
                "order_by": "",
                "page_number": 1,
                "total_records_per_page": config.settings.page_size,
            }
            headers["page_info"] = json.dumps(pi, separators=(",", ":"))

        return headers

    def _get_params(self, params: dict | None = None) -> dict:
        base_params = {"locale": config.settings.locale}
        if params:
            base_params.update(params)
        return base_params

    async def get(
        self,
        path: str,
        params: dict | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}{path}"
        headers = self._get_headers("GET")
        final_params = self._get_params(params)

        if client:
            response = await client.get(url, headers=headers, params=final_params)
        else:
            async with httpx.AsyncClient() as c:
                response = await c.get(url, headers=headers, params=final_params)

        response.raise_for_status()
        data = response.json()
        self._check_response(data)
        return data

    async def post(
        self,
        path: str,
        json_body: dict,
        params: dict | None = None,
        page_info: dict | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}{path}"
        headers = self._get_headers("POST", page_info=page_info)
        final_params = self._get_params(params)

        if client:
            response = await client.post(
                url, headers=headers, params=final_params, json=json_body
            )
        else:
            async with httpx.AsyncClient() as c:
                response = await c.post(
                    url, headers=headers, params=final_params, json=json_body
                )

        response.raise_for_status()
        data = response.json()
        self._check_response(data)
        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_response(self, data: dict) -> None:
        """Check the API response for errors."""
        headers = data.get("headers", {})
        code = headers.get("response_code", "0000")
        # 0001 means "no results" which is not an error for search
        if code not in ("0000", "0001"):
            message = headers.get("response_message", "Unknown error")
            raise APIError(code, message)

    def _update_cookies_from_response(self, response: httpx.Response) -> None:
        """Merge Set-Cookie headers from *response* into ``session_cookie``."""
        existing = _parse_cookie_header(self.session_cookie)

        for raw_header in response.headers.get_list("set-cookie"):
            # Each Set-Cookie header looks like:
            #   name=value; Path=/; Domain=...; HttpOnly; Secure
            # We only need the name=value portion (before the first ";").
            cookie_part = raw_header.split(";", 1)[0].strip()
            if "=" in cookie_part:
                name, value = cookie_part.split("=", 1)
                existing[name.strip()] = value.strip()

        self.session_cookie = "; ".join(f"{k}={v}" for k, v in existing.items())


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _parse_cookie_header(cookie_str: str) -> dict[str, str]:
    """Parse a ``Cookie`` header string into a ``{name: value}`` dict."""
    cookies: dict[str, str] = {}
    if not cookie_str:
        return cookies
    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


def _serialize_cookie_jar(jar: httpx.Cookies) -> str:
    """Serialize an httpx cookie jar into a ``Cookie`` header string."""
    return "; ".join(f"{name}={value}" for name, value in jar.items())
