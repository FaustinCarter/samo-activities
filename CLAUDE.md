# CLAUDE.md — Santa Monica Activities Browser

## What This Is
A FastAPI web app that replaces the clunky ActiveNet website for browsing Santa Monica recreation activities. Shows activity metadata (days, times, location, availability) upfront in card and calendar views, eliminating the need to click into each activity's detail page.

## Tech Stack
- **Python 3.12+**, **FastAPI**, **Jinja2** templates, **Pydantic v2** models
- **httpx** (async HTTP client), **nh3** (HTML sanitization)
- **uv** for package management (`uv.lock`) and running all Python tools
- No database — read-only client against ActiveNet REST API

## Project Layout
```
app/
├── main.py              # FastAPI app init, middleware, template filters
├── config.py            # Pydantic Settings (BASE_URL, port, locale, page_size)
├── client.py            # ActiveNetClient: HTTP wrapper, bootstrap, login, API calls
├── sessions.py          # In-memory per-user session store (keyed by cookie)
├── deps.py              # Session middleware + FastAPI dependency injection
├── calendar.py          # Calendar building, pattern expansion, date math
├── models/
│   ├── activity.py      # ActivityItem, ActivityDetail, filters, pricing, etc.
│   └── common.py        # PageInfo, response envelope
├── routes/
│   ├── activities.py    # GET / (browse), GET /activity/{id} (detail)
│   └── auth.py          # GET/POST /login, GET /logout
├── services/
│   └── activities.py    # Business logic: search, filters, details, meeting dates
├── templates/           # Jinja2 HTML templates
└── static/              # style.css, calendar.js
tests/
├── unit/                # Calendar logic, model validation
├── integration/         # Route + service tests with mocked HTTP (respx)
├── e2e/                 # Playwright browser tests
└── conftest.py          # Shared fixtures
docs/
└── santa-monica-recreation-api-docs.md   # ActiveNet API reference
```

## Commands
```bash
uv run python -m app.main          # Run dev server (localhost:8000)
uv run pytest                      # All tests
uv run pytest tests/unit           # Unit tests only
uv run pytest tests/integration    # Integration tests (mocked HTTP)
uv run pytest tests/e2e            # E2E tests (Playwright)
uv run ruff check app/             # Lint
uv run ruff format app/            # Format
uv run mypy app/                   # Type check
```

## Key Architecture
- **Async throughout**: All routes and services use async/await. Routes use `asyncio.gather()` for parallel data fetching.
- **Per-user session isolation**: Each visitor gets their own `ActiveNetClient` instance with independent cookies/tokens. Sessions are ephemeral (lost on restart).
- **Anonymous bootstrap**: First visit auto-creates a session by fetching ActiveNet's signin page to extract CSRF token and cookies.
- **Service layer pattern**: Routes → services → client → ActiveNet API. Services return `None` on failure (graceful degradation).
- **Dependency injection**: `request.state.api_client` set by middleware, retrieved via `Depends(get_api_client)`.
- **Meeting dates are lazy**: Only fetched for calendar view or `show_full_details=true` (expensive call).

## ActiveNet API
- Base URL configured in `.env` as `BASE_URL`
- All requests include `locale=en-US` query param
- Response envelope: `{headers, body}` — services unwrap the `body`
- CSRF token required in `X-CSRF-Token` header for POST requests
- Key endpoints: `/rest/activities/list` (search), `/rest/activities/filters`, `/rest/activity/detail/{id}`, `/rest/user/signin`

## Conventions
### Import Rules — Google Python Style Guide

#### Core Principles
- Use `import` statements to import **packages and modules only**.
- Do **not** import individual classes, functions, or variables directly unless explicitly allowed (see exceptions below).

#### Preferred Import Forms
- Use `import x` for modules and packages.
- Use `from x import y` only when `y` is a **module** within package `x`.
- Use `from x import y as z` when:
  - Two imported modules share the same name.
  - The imported name conflicts with a local name.
  - The imported name is overly long or unclear in context.
- Use `import x as y` only for **widely accepted abbreviations** (e.g., `import numpy as np`).

#### Avoid Relative Imports
- Do **not** use relative imports (e.g., `from . import foo`).
- Always use the full package path to prevent ambiguity and duplicate imports.

#### Exceptions
- Importing individual symbols is allowed for modules used primarily for:
  - Static analysis
  - Type checking  
  (e.g., `typing`, `collections.abc`, `typing_extensions`)

### Other conventions
- Pydantic models for all API data (`app/models/`)
- `TypedDict` for presentation-layer calendar structures
- HTML sanitization via `sanitize_html` Jinja2 filter (uses `nh3`)
- Password handling: never stored, only passed as function params, single-use
- Tests use `respx` to mock httpx requests; fixtures in `conftest.py`
