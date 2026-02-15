import asyncio

import httpx

from app import client as client_module
from app.models import activity as activity_models
from app.models import common as common_models


async def get_filters(
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> activity_models.ActivityFilterOptions:
    """Fetch filter options for the activity search UI."""
    if api_client is None:
        api_client = client_module.api_client

    data = await api_client.get("/activities/filters", client=http_client)
    body = data.get("body", {})
    return activity_models.ActivityFilterOptions.model_validate(body)


async def search(
    pattern: activity_models.ActivitySearchPattern,
    page_number: int = 1,
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> tuple[list[activity_models.ActivityItem], common_models.PageInfo]:
    """Search for activities with the given filters."""
    if api_client is None:
        api_client = client_module.api_client

    request = activity_models.ActivitySearchRequest(activity_search_pattern=pattern)
    page_info = {
        "order_by": "",
        "page_number": page_number,
        "total_records_per_page": 20,
    }

    data = await api_client.post(
        "/activities/list",
        json_body=request.model_dump(),
        page_info=page_info,
        client=http_client,
    )

    headers = data.get("headers", {})
    page_info = common_models.PageInfo.model_validate(headers.get("page_info", {}))

    body = data.get("body", {})
    items_data = body.get("activity_items", [])

    items = [activity_models.ActivityItem.model_validate(item) for item in items_data]

    return items, page_info


async def get_meeting_dates(
    activity_id: int,
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> activity_models.MeetingAndRegistrationDates | None:
    """Fetch meeting dates for a single activity."""
    if api_client is None:
        api_client = client_module.api_client

    try:
        data = await api_client.get(
            f"/activity/detail/meetingandregistrationdates/{activity_id}",
            client=http_client,
        )
        body = data.get("body", {})
        meeting_data = body.get("meeting_and_registration_dates", {})
        if meeting_data:
            return activity_models.MeetingAndRegistrationDates.model_validate(
                meeting_data
            )
    except Exception:
        # If we can't get meeting dates, just return None
        pass
    return None


async def get_meeting_dates_batch(
    activity_ids: list[int],
    api_client: client_module.ActiveNetClient | None = None,
) -> dict[int, activity_models.MeetingAndRegistrationDates]:
    """Fetch meeting dates for multiple activities in parallel."""
    if not activity_ids:
        return {}

    if api_client is None:
        api_client = client_module.api_client

    async with httpx.AsyncClient() as http_client:
        tasks = [
            get_meeting_dates(aid, api_client=api_client, http_client=http_client)
            for aid in activity_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates] = {}
    for aid, result in zip(activity_ids, results):
        if isinstance(result, activity_models.MeetingAndRegistrationDates):
            meeting_dates[aid] = result

    return meeting_dates
