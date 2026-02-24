"""FastAPI dependencies for session management and client injection."""

import fastapi

from app.client import ActiveNetClient


async def session_middleware(
    request: fastapi.Request,
    call_next,
):
    """Resolve or create a session, then set the cookie on the real response.

    Unlike a ``Depends`` that injects ``Response``, middleware has access to the
    actual response object that will be sent to the browser, so the cookie is
    guaranteed to be delivered.
    """
    session_manager = request.app.state.session_manager
    session_id = request.cookies.get("samo_session")

    client = session_manager.get_client(session_id) if session_id else None
    new_session_id = None

    if client is None:
        new_session_id, client = await session_manager.create_session()

    # Stash the client on request.state so routes can access it.
    request.state.api_client = client

    response = await call_next(request)

    if new_session_id is not None:
        response.set_cookie(
            "samo_session",
            new_session_id,
            httponly=True,
            samesite="lax",
        )

    return response


async def get_api_client(
    request: fastapi.Request,
) -> ActiveNetClient:
    """Retrieve the API client set by :func:`session_middleware`."""
    return request.state.api_client
