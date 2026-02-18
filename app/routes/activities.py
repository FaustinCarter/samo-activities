import asyncio
import typing

import fastapi

from app.calendar import build_calendar_data, build_query_string
from app.models import activity as activity_models
from app.services import activities as activities_service

router = fastapi.APIRouter()


@router.get("/")
async def browse_activities(
    request: fastapi.Request,
    q: str = "",
    date_after: str = "",
    date_before: str = "",
    category_ids: typing.Annotated[list[int] | None, fastapi.Query()] = None,
    center_ids: typing.Annotated[list[int] | None, fastapi.Query()] = None,
    show_full_details: bool = False,
    view: str = "card",
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

    filters, (activities, page_info) = await asyncio.gather(filters_task, search_task)

    # Meeting dates are needed for calendar view (to expand patterns to dates)
    # and optionally for card view when show_full_details is on.
    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates] = {}
    prices: dict[int, activity_models.EstimatedPrice] = {}

    if activities:
        activity_ids = [a.id for a in activities]
        need_meeting_dates = show_full_details or view == "calendar"
        need_prices = show_full_details

        if need_meeting_dates and need_prices:
            meeting_dates, prices = await asyncio.gather(
                activities_service.get_meeting_dates_batch(activity_ids),
                activities_service.get_prices_batch(activity_ids),
            )
        elif need_meeting_dates:
            meeting_dates = await activities_service.get_meeting_dates_batch(
                activity_ids
            )
        elif need_prices:
            prices = await activities_service.get_prices_batch(activity_ids)

    params = {
        "q": q,
        "date_after": date_after,
        "date_before": date_before,
        "category_ids": category_ids or [],
        "center_ids": center_ids or [],
        "show_full_details": show_full_details,
        "view": view,
    }

    def pagination_query(target_page: int) -> str:
        return build_query_string(params, target_page)

    # Build calendar data structure (empty list if not in calendar view)
    calendar_months = []
    if view == "calendar" and activities:
        calendar_months = build_calendar_data(activities, meeting_dates)

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
            "calendar_months": calendar_months,
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
