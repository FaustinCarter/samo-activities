import asyncio
import logging

import httpx

from app import client as client_module
from app.models import activity as activity_models
from app.models import common as common_models

logger = logging.getLogger(__name__)


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
            logger.info(
                "meeting_and_registration_dates keys for %s: %s",
                activity_id,
                list(meeting_data.keys()),
            )
            logger.debug("meeting_and_registration_dates for %s: %s", activity_id, meeting_data)
            return activity_models.MeetingAndRegistrationDates.model_validate(
                meeting_data
            )
    except Exception:
        logger.exception("Failed to fetch meeting dates for %s", activity_id)
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


async def get_activity_detail(
    activity_id: int,
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> activity_models.ActivityDetail | None:
    """Fetch full detail for a single activity."""
    if api_client is None:
        api_client = client_module.api_client

    try:
        data = await api_client.get(
            f"/activity/detail/{activity_id}",
            client=http_client,
        )
        body = data.get("body", {})
        detail_data = body.get("detail", {})
        if detail_data:
            logger.info(
                "activity/detail keys for %s: %s",
                activity_id,
                list(detail_data.keys()),
            )
            logger.debug("activity/detail for %s: %s", activity_id, detail_data)
            return activity_models.ActivityDetail.model_validate(detail_data)
    except Exception:
        logger.exception("Failed to fetch activity detail for %s", activity_id)
    return None


async def get_activity_price(
    activity_id: int,
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> activity_models.EstimatedPrice | None:
    """Fetch pricing info for a single activity."""
    if api_client is None:
        api_client = client_module.api_client

    try:
        data = await api_client.get(
            f"/activity/detail/estimateprice/{activity_id}",
            client=http_client,
        )
        body = data.get("body", {})
        price_data = body.get("estimateprice", {})
        if price_data:
            logger.info(
                "estimateprice keys for %s: %s",
                activity_id,
                list(price_data.keys()),
            )
            logger.debug("estimateprice for %s: %s", activity_id, price_data)
            return activity_models.EstimatedPrice.model_validate(price_data)
    except Exception:
        logger.exception("Failed to fetch price for %s", activity_id)
    return None


async def get_prices_batch(
    activity_ids: list[int],
    api_client: client_module.ActiveNetClient | None = None,
) -> dict[int, activity_models.EstimatedPrice]:
    """Fetch prices for multiple activities in parallel."""
    if not activity_ids:
        return {}

    if api_client is None:
        api_client = client_module.api_client

    async with httpx.AsyncClient() as http_client:
        tasks = [
            get_activity_price(aid, api_client=api_client, http_client=http_client)
            for aid in activity_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    prices: dict[int, activity_models.EstimatedPrice] = {}
    for aid, result in zip(activity_ids, results):
        if isinstance(result, activity_models.EstimatedPrice):
            prices[aid] = result

    return prices


async def get_button_status(
    activity_id: int,
    api_client: client_module.ActiveNetClient | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> activity_models.ButtonStatus | None:
    """Fetch the current enrollment button status for an activity."""
    if api_client is None:
        api_client = client_module.api_client

    try:
        data = await api_client.get(
            f"/activity/detail/buttonstatus/{activity_id}",
            client=http_client,
        )
        body = data.get("body", {})
        status_data = body.get("button_status", {})
        if status_data:
            logger.info(
                "buttonstatus keys for %s: %s",
                activity_id,
                list(status_data.keys()),
            )
            logger.debug("buttonstatus for %s: %s", activity_id, status_data)
            return activity_models.ButtonStatus.model_validate(status_data)
    except Exception:
        logger.exception("Failed to fetch button status for %s", activity_id)
    return None
