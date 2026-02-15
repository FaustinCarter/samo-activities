import asyncio
import typing
import urllib.parse

import fastapi
from fastapi import templating

from app.models import activity as activity_models
from app.services import activities as activities_service

router = fastapi.APIRouter()


def build_query_string(params: dict, page: int) -> str:
    """Build a query string from params dict with a specific page number."""
    query_params = []

    if params.get("q"):
        query_params.append(("q", params["q"]))
    if params.get("date_after"):
        query_params.append(("date_after", params["date_after"]))
    if params.get("date_before"):
        query_params.append(("date_before", params["date_before"]))
    for cat_id in params.get("category_ids", []):
        query_params.append(("category_ids", str(cat_id)))
    for center_id in params.get("center_ids", []):
        query_params.append(("center_ids", str(center_id)))
    if params.get("show_schedule"):
        query_params.append(("show_schedule", "true"))

    query_params.append(("page", str(page)))

    return urllib.parse.urlencode(query_params)


@router.get("/")
async def browse_activities(
    request: fastapi.Request,
    q: str = "",
    date_after: str = "",
    date_before: str = "",
    category_ids: typing.Annotated[list[int], fastapi.Query()] = None,
    center_ids: typing.Annotated[list[int], fastapi.Query()] = None,
    show_schedule: bool = False,
    page: int = 1,
):
    """Browse and search activities with filters."""
    # Build search pattern from query params
    pattern = activity_models.ActivitySearchPattern(
        activity_keyword=q,
        date_after=date_after,
        date_before=date_before,
        activity_category_ids=category_ids or [],
        center_ids=center_ids or [],
    )

    # Fetch filters and search results in parallel
    filters_task = activities_service.get_filters()
    search_task = activities_service.search(pattern, page_number=page)

    filters, (activities, page_info) = await asyncio.gather(
        filters_task, search_task
    )

    # Optionally fetch meeting dates for schedule display
    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates] = {}
    if show_schedule and activities:
        activity_ids = [a.id for a in activities]
        meeting_dates = await activities_service.get_meeting_dates_batch(activity_ids)

    # Build current params for pagination links
    params = {
        "q": q,
        "date_after": date_after,
        "date_before": date_before,
        "category_ids": category_ids or [],
        "center_ids": center_ids or [],
        "show_schedule": show_schedule,
    }

    # Create pagination helper
    def pagination_query(target_page: int) -> str:
        return build_query_string(params, target_page)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "activities": activities,
            "meeting_dates": meeting_dates,
            "filters": filters,
            "page_info": page_info,
            "params": params,
            "current_page": page,
            "pagination_query": pagination_query,
        },
    )
