"""Login and logout routes."""

import logging

import fastapi
from fastapi.responses import RedirectResponse

from app.client import APIError, ActiveNetClient
from app.deps import get_api_client

logger = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.get("/login")
async def login_page(
    request: fastapi.Request,
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
):
    """Render the login form.  Redirects to ``/`` if already authenticated."""
    if api_client.is_authenticated:
        return RedirectResponse("/", status_code=303)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "login.html",
        {"api_client": api_client, "error": None},
    )


@router.post("/login")
async def login_submit(
    request: fastapi.Request,
    username: str = fastapi.Form(...),
    password: str = fastapi.Form(...),
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
):
    """Process the login form.

    The *password* parameter is a local variable in this handler.  It is passed
    directly to :meth:`ActiveNetClient.login` (which sends it to the upstream
    API in a single HTTPS POST) and is never stored, logged, or persisted in
    any form.
    """
    try:
        await api_client.login(username, password)
        # password is no longer referenced after this line.
        return RedirectResponse("/", status_code=303)
    except APIError as exc:
        logger.warning("Login failed for %s: %s", username, exc.message)
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "login.html",
            {"api_client": api_client, "error": exc.message},
            status_code=401,
        )
    except Exception:
        logger.exception("Unexpected error during login for %s", username)
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "login.html",
            {"api_client": api_client, "error": "Login failed. Please try again."},
            status_code=500,
        )


@router.get("/logout")
async def logout(request: fastapi.Request):
    """Destroy the current session and redirect to the homepage."""
    session_manager = request.app.state.session_manager
    session_id = request.cookies.get("samo_session")

    if session_id:
        session_manager.destroy_session(session_id)

    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("samo_session")
    return response
