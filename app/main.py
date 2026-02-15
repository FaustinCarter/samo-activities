import pathlib
import urllib.parse

import fastapi
from fastapi import staticfiles
from fastapi import templating

from app.routes import activities as activities_routes


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI(title="Santa Monica Activities")

    # Setup templates
    templates_dir = pathlib.Path(__file__).parent / "templates"
    templates = templating.Jinja2Templates(directory=str(templates_dir))

    # Add custom template function for pagination
    def pagination_query(page: int) -> str:
        """Build query string for pagination links, preserving current filters."""
        # This will be called from within the request context
        # We'll inject the params via the template context
        return ""

    templates.env.globals["pagination_query"] = pagination_query

    app.state.templates = templates

    # Mount static files
    static_dir = pathlib.Path(__file__).parent.parent / "static"
    app.mount("/static", staticfiles.StaticFiles(directory=str(static_dir)), name="static")

    # Include routes
    app.include_router(activities_routes.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
