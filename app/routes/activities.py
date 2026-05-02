import asyncio
import typing

import fastapi

from app.calendar import build_calendar_data, build_query_string
from app.client import ActiveNetClient
from app.deps import get_api_client
from app.models import activity as activity_models
from app.models import common as common_models
from app.services import activities as activities_service

router = fastapi.APIRouter()


@router.get("/")
async def browse_activities(
    request: fastapi.Request,
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
    q: str = "",
    date_after: str = "",
    date_before: str = "",
    category_ids: typing.Annotated[list[int] | None, fastapi.Query()] = None,
    center_ids: typing.Annotated[list[int] | None, fastapi.Query()] = None,
    wishlist_only: bool = False,
    view: str = "card",
    page: int = 1,
):
    """Browse and search activities with filters."""
    if wishlist_only and api_client.is_authenticated:
        filters_task = activities_service.get_filters(api_client)
        wishlist_task = activities_service.get_wishlist(api_client)
        filters, activities = await asyncio.gather(filters_task, wishlist_task)
        page_info = common_models.PageInfo(
            total_records=len(activities),
            total_page=1,
            page_number=1,
            total_records_per_page=len(activities) or 20,
        )
    else:
        wishlist_only = False
        pattern = activity_models.ActivitySearchPattern(
            activity_keyword=q,
            date_after=date_after,
            date_before=date_before,
            activity_category_ids=category_ids or [],
            center_ids=center_ids or [],
        )

        # Fetch filters and search results in parallel
        filters_task = activities_service.get_filters(api_client)
        search_task = activities_service.search(api_client, pattern, page_number=page)

        filters, (activities, page_info) = await asyncio.gather(
            filters_task, search_task
        )

    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates] = {}
    prices: dict[int, activity_models.EstimatedPrice] = {}
    button_statuses: dict[int, activity_models.ButtonStatus] = {}

    if activities:
        activity_ids = [a.id for a in activities]
        button_statuses, meeting_dates, prices = await asyncio.gather(
            activities_service.get_button_status_batch(api_client, activity_ids),
            activities_service.get_meeting_dates_batch(api_client, activity_ids),
            activities_service.get_prices_batch(api_client, activity_ids),
        )

    params = {
        "q": q,
        "date_after": date_after,
        "date_before": date_before,
        "category_ids": category_ids or [],
        "center_ids": center_ids or [],
        "wishlist_only": wishlist_only,
        "view": view,
    }

    def pagination_query(target_page: int) -> str:
        return build_query_string(params, target_page)

    # Build calendar data structure (empty list if not in calendar view)
    calendar_months = []
    if view == "calendar" and activities:
        calendar_months = build_calendar_data(
            activities, meeting_dates, button_statuses
        )

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "api_client": api_client,
            "activities": activities,
            "meeting_dates": meeting_dates,
            "prices": prices,
            "button_statuses": button_statuses,
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
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
):
    """Display the full detail page for a single activity."""
    detail_task = activities_service.get_activity_detail(api_client, activity_id)
    meeting_task = activities_service.get_meeting_dates(api_client, activity_id)
    price_task = activities_service.get_activity_price(api_client, activity_id)
    button_task = activities_service.get_button_status(api_client, activity_id)

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
            "api_client": api_client,
            "detail": detail,
            "meeting_dates": meeting_dates,
            "price": price,
            "button_status": button_status,
        },
    )


@router.post("/api/wishlist/{activity_id}")
async def api_add_to_wishlist(
    activity_id: int,
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
):
    """Add an activity to the wishlist (AJAX endpoint)."""
    if not api_client.is_authenticated:
        raise fastapi.HTTPException(status_code=401, detail="Login required")
    wish_list_id = await activities_service.add_to_wishlist(api_client, activity_id)
    if wish_list_id is None:
        raise fastapi.HTTPException(status_code=500, detail="Failed to add to wishlist")
    return {"wish_list_id": wish_list_id}


@router.delete("/api/wishlist/{wish_list_id}")
async def api_remove_from_wishlist(
    wish_list_id: int,
    api_client: ActiveNetClient = fastapi.Depends(get_api_client),
):
    """Remove an item from the wishlist (AJAX endpoint)."""
    if not api_client.is_authenticated:
        raise fastapi.HTTPException(status_code=401, detail="Login required")
    success = await activities_service.remove_from_wishlist(api_client, wish_list_id)
    if not success:
        raise fastapi.HTTPException(
            status_code=500, detail="Failed to remove from wishlist"
        )
    return {"success": True}
