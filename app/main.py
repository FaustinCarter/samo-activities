import datetime
import hashlib
import logging
import pathlib

import fastapi
import nh3
from fastapi import staticfiles
from fastapi import templating

from app import config
from starlette.middleware.base import BaseHTTPMiddleware

from app.deps import session_middleware
from app.routes import activities as activities_routes
from app.routes import auth as auth_routes
from app.sessions import SessionManager

logging.basicConfig(level=logging.INFO)


def _format_date(value: str) -> str:
    """Format an ISO date string (YYYY-MM-DD) to a readable form (e.g. Mar 30, 2026)."""
    if not value:
        return ""
    try:
        dt = datetime.datetime.strptime(value, "%Y-%m-%d")
        # %-d removes the leading zero on Linux; use %#d on Windows
        return dt.strftime("%b %-d, %Y")
    except ValueError:
        return value


def _sanitize_html(value: str) -> str:
    """Sanitize HTML, keeping only safe tags and attributes."""
    if not value:
        return ""
    return nh3.clean(value)


def _activity_code_color(value: str) -> str:
    """Hash an activity code (e.g. "1201.101") to a stable HSL color.

    Activities sharing the same prefix (the part before the dot) get the same
    color, so visually grouping related sessions in the listing.
    """
    if not value:
        return "hsl(195, 12%, 47%)"
    prefix = value.split(".", 1)[0] or value
    digest = hashlib.md5(prefix.encode("utf-8")).hexdigest()
    hue = int(digest[:8], 16) % 360
    return f"hsl({hue}, 55%, 42%)"


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI(title="SaMo Rec: Activity Browser")

    # Session manager — in-memory store of per-user ActiveNetClient instances
    app.state.session_manager = SessionManager()

    # Setup templates
    templates_dir = pathlib.Path(__file__).parent / "templates"
    templates = templating.Jinja2Templates(directory=str(templates_dir))

    # Custom filters
    templates.env.filters["format_date"] = _format_date
    templates.env.filters["sanitize_html"] = _sanitize_html
    templates.env.filters["activity_code_color"] = _activity_code_color

    # Template globals
    templates.env.globals["original_site_link"] = config.settings.original_site_link

    app.state.templates = templates

    # Mount static files
    static_dir = pathlib.Path(__file__).parent / "static"
    app.mount(
        "/static", staticfiles.StaticFiles(directory=str(static_dir)), name="static"
    )

    # Session middleware — resolves/creates sessions and sets the cookie
    app.add_middleware(BaseHTTPMiddleware, dispatch=session_middleware)

    # Include routes
    app.include_router(auth_routes.router)
    app.include_router(activities_routes.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.settings.host,
        port=config.settings.port,
        reload=True,
    )
