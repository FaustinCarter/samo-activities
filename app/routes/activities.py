import asyncio
import typing
import urllib.parse

import fastapi

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
    if params.get("show_full_details"):
        query_params.append(("show_full_details", "true"))

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
    show_full_details: bool = False,
    page: int = 1,
):
    """Browse and search activities with filters."""
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

    # Optionally fetch meeting dates and prices for all cards on the page
    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates] = {}
    prices: dict[int, activity_models.EstimatedPrice] = {}
    if show_full_details and activities:
        activity_ids = [a.id for a in activities]
        meeting_dates, prices = await asyncio.gather(
            activities_service.get_meeting_dates_batch(activity_ids),
            activities_service.get_prices_batch(activity_ids),
        )

    params = {
        "q": q,
        "date_after": date_after,
        "date_before": date_before,
        "category_ids": category_ids or [],
        "center_ids": center_ids or [],
        "show_full_details": show_full_details,
    }

    def pagination_query(target_page: int) -> str:
        return build_query_string(params, target_page)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "activities": activities,
            "meeting_dates": meeting_dates,
            "prices": prices,
            "filters": filters,
            "page_info": page_info,
            "params": params,
            "current_page": page,
            "pagination_query": pagination_query,
        },
    )


@router.get("/activity/{activity_id}")
async def activity_detail(
    request: fastapi.Request,
    activity_id: int,
):
    """Display the full detail page for a single activity."""
    detail_task = activities_service.get_activity_detail(activity_id)
    meeting_task = activities_service.get_meeting_dates(activity_id)
    price_task = activities_service.get_activity_price(activity_id)
    button_task = activities_service.get_button_status(activity_id)

    detail, meeting_dates, price, button_status = await asyncio.gather(
        detail_task, meeting_task, price_task, button_task
    )

    if detail is None:
        raise fastapi.HTTPException(status_code=404, detail="Activity not found")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "activity_detail.html",
        {
            "detail": detail,
            "meeting_dates": meeting_dates,
            "price": price,
            "button_status": button_status,
        },
    )
