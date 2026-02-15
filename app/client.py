import json

import httpx

from app import config

_BASE_SITE_URL = "https://anc.apm.activecommunities.com/santamonicarecreation"
_REFERER = (
    f"{_BASE_SITE_URL}/activity/search"
    "?onlineSiteId=0&activity_select_param=2&viewMode=list"
)


class APIError(Exception):
    """Raised when the upstream API returns a non-success response code."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API Error {code}: {message}")


class ActiveNetClient:
    """HTTP client wrapper for the ActiveNet REST API."""

    def __init__(self):
        self.base_url = config.settings.base_url
        self.session_cookie = config.settings.session_cookie
        self.csrf_token = config.settings.csrf_token

    def _get_headers(
        self,
        method: str = "GET",
        page_info: dict | None = None,
    ) -> dict[str, str]:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "Origin": _BASE_SITE_URL,
            "Referer": _REFERER,
        }
        if self.session_cookie:
            headers["Cookie"] = self.session_cookie

        if method == "GET":
            headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
        elif method == "POST":
            headers["Content-Type"] = "application/json;charset=utf-8"
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            # The API controls pagination via a page_info request header (not a query
            # param), matching exactly what the browser sends.
            pi = page_info or {
                "order_by": "",
                "page_number": 1,
                "total_records_per_page": 20,
            }
            headers["page_info"] = json.dumps(pi, separators=(",", ":"))

        return headers

    def _get_params(self, params: dict | None = None) -> dict:
        base_params = {"locale": "en-US"}
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

    def _check_response(self, data: dict) -> None:
        """Check the API response for errors."""
        headers = data.get("headers", {})
        code = headers.get("response_code", "0000")
        # 0001 means "no results" which is not an error for search
        if code not in ("0000", "0001"):
            message = headers.get("response_message", "Unknown error")
            raise APIError(code, message)


# Singleton instance
api_client = ActiveNetClient()
