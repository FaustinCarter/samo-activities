import datetime
import logging
import pathlib

import fastapi
import nh3
from fastapi import staticfiles
from fastapi import templating

from app import config
from app.routes import activities as activities_routes

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


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI(title="Santa Monica Activities")

    # Setup templates
    templates_dir = pathlib.Path(__file__).parent / "templates"
    templates = templating.Jinja2Templates(directory=str(templates_dir))

    # Custom filters
    templates.env.filters["format_date"] = _format_date
    templates.env.filters["sanitize_html"] = _sanitize_html

    app.state.templates = templates

    # Mount static files
    static_dir = pathlib.Path(__file__).parent / "static"
    app.mount(
        "/static", staticfiles.StaticFiles(directory=str(static_dir)), name="static"
    )

    # Include routes
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
