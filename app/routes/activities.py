import asyncio
import calendar
import datetime
import typing
import urllib.parse

import fastapi

from app.models import activity as activity_models
from app.services import activities as activities_service

router = fastapi.APIRouter()

# Palette of 20 distinct colors for activity pills on the calendar.
# Each activity gets a stable color by (activity_id % len(PILL_COLORS)).
# With 20 colors and default page size of 20, each activity gets a unique color.
PILL_COLORS = [
    "#1a5276",  # navy
    "#117a65",  # teal
    "#784212",  # brown
    "#6c3483",  # purple
    "#1a618f",  # blue
    "#922b21",  # red
    "#7d6608",  # olive
    "#1e8449",  # green
    "#d35400",  # orange
    "#2e4053",  # slate
    "#148f77",  # cyan
    "#b03a2e",  # crimson
    "#1f618d",  # steel blue
    "#7b241c",  # maroon
    "#196f3d",  # forest
    "#a04000",  # rust
    "#4a235a",  # plum
    "#0e6655",  # dark teal
    "#7e5109",  # bronze
    "#2874a6",  # cobalt
]

WEEKDAY_ABBR_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _parse_iso(s: str) -> datetime.date | None:
    """Parse an ISO date string (YYYY-MM-DD) to a date, or None on failure."""
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(s[:10])
    except ValueError:
        return None


def _parse_weekdays(weekdays_str: str) -> list[int]:
    """
    Parse a weekdays string like "Mon, Wed, Fri" into a list of weekday
    integers (0=Monday … 6=Sunday).
    """
    result = []
    for part in weekdays_str.split(","):
        key = part.strip().lower()[:3]
        if key in WEEKDAY_ABBR_MAP:
            result.append(WEEKDAY_ABBR_MAP[key])
    return result


def _expand_pattern_dates(
    pattern: activity_models.ActivityPattern,
) -> set[datetime.date]:
    """
    Expand an ActivityPattern into the full set of individual dates on which
    this pattern's sessions occur.
    """
    start = _parse_iso(pattern.beginning_date)
    end = _parse_iso(pattern.ending_date)
    if start is None or end is None:
        return set()

    # Collect exception dates
    exception_dates: set[datetime.date] = set()
    for exc in pattern.exception_dates or []:
        if isinstance(exc, str):
            d = _parse_iso(exc)
            if d:
                exception_dates.add(d)
        elif isinstance(exc, dict):
            d = _parse_iso(exc.get("date", ""))
            if d:
                exception_dates.add(d)

    # Collect all weekday numbers across all pattern_dates entries
    all_weekdays: set[int] = set()
    for pd in pattern.pattern_dates:
        all_weekdays.update(_parse_weekdays(pd.weekdays))

    # Parse weeks_of_month filter (e.g. "1, 3" means 1st and 3rd week)
    weeks_of_month: set[int] | None = None
    if pattern.weeks_of_month:
        parsed = set()
        for part in pattern.weeks_of_month.split(","):
            part = part.strip()
            if part.isdigit():
                parsed.add(int(part))
        if parsed:
            weeks_of_month = parsed

    dates: set[datetime.date] = set()
    current = start
    delta = datetime.timedelta(days=1)
    while current <= end:
        if current.weekday() in all_weekdays and current not in exception_dates:
            if weeks_of_month is not None:
                # Which occurrence of this weekday is it in the month?
                # "1st Monday", "2nd Monday", etc.
                occurrence = (current.day - 1) // 7 + 1
                if occurrence in weeks_of_month:
                    dates.add(current)
            else:
                dates.add(current)
        current += delta
    return dates


def _activity_meeting_dates(
    activity: activity_models.ActivityItem,
    meeting_info: activity_models.MeetingAndRegistrationDates | None,
) -> set[datetime.date]:
    """
    Return the full set of individual meeting dates for an activity.
    Falls back to the activity's date_range_start if no meeting_info is available.
    """
    if meeting_info is None or meeting_info.no_meeting_dates:
        d = _parse_iso(activity.date_range_start)
        return {d} if d else set()

    dates: set[datetime.date] = set()
    for pattern in meeting_info.activity_patterns:
        dates.update(_expand_pattern_dates(pattern))

    # If patterns gave us nothing, fall back to start date
    if not dates:
        d = _parse_iso(activity.date_range_start)
        if d:
            dates.add(d)

    return dates


def build_calendar_data(
    activities: list[activity_models.ActivityItem],
    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates],
) -> list[dict]:
    """
    Build a list of month dicts for the calendar template.

    Each month dict has:
        year, month, name, weeks
    Each week is a list of 7 day-dicts:
        day (int), in_month (bool), iso_date (str), events (list of event dicts)
    Each event dict has:
        id, name, color, location, ages, total_open, action_link_href,
        action_link_label, date_range_start, date_range_end,
        starting_time, ending_time
    """
    today = datetime.date.today()

    if not activities:
        return []

    # Map activity_id -> list[dict] for calendar events, and collect all dates
    event_by_date: dict[datetime.date, list[dict]] = {}
    earliest_date: datetime.date | None = None
    latest_date: datetime.date | None = None

    for index, activity in enumerate(activities):
        color = PILL_COLORS[index % len(PILL_COLORS)]
        meeting_info = meeting_dates.get(activity.id)

        # Collect time info from patterns
        time_slots: list[tuple[str, str]] = []
        if meeting_info:
            for pattern in meeting_info.activity_patterns:
                for pd in pattern.pattern_dates:
                    if pd.starting_time:
                        time_slots.append((pd.starting_time, pd.ending_time))

        # Deduplicate time slots
        seen_slots: set[tuple[str, str]] = set()
        unique_slots: list[tuple[str, str]] = []
        for slot in time_slots:
            if slot not in seen_slots:
                seen_slots.add(slot)
                unique_slots.append(slot)

        starting_time = unique_slots[0][0][:5] if unique_slots else ""
        ending_time = unique_slots[0][1][:5] if unique_slots else ""

        event = {
            "id": activity.id,
            "name": activity.name,
            "color": color,
            "location": activity.location.label if activity.location else "",
            "ages": activity.ages,
            "total_open": activity.total_open,
            "action_link_href": activity.action_link.href if activity.action_link else "",
            "action_link_label": activity.action_link.label if activity.action_link else "Enroll",
            "date_range_start": activity.date_range_start,
            "date_range_end": activity.date_range_end,
            "starting_time": starting_time,
            "ending_time": ending_time,
            "number": activity.number,
        }

        all_dates = _activity_meeting_dates(activity, meeting_info)

        for d in all_dates:
            if d not in event_by_date:
                event_by_date[d] = []
            event_by_date[d].append(event)
            if earliest_date is None or d < earliest_date:
                earliest_date = d
            if latest_date is None or d > latest_date:
                latest_date = d

    # If no events found, return empty calendar
    if earliest_date is None or latest_date is None:
        return []

    # Determine month range: first month with events through last month with events
    start_month = earliest_date.replace(day=1)
    end_month = latest_date.replace(day=1)

    months = []
    cur_month = start_month
    while cur_month <= end_month:
        year = cur_month.year
        month = cur_month.month
        month_name = cur_month.strftime("%B %Y")

        # calendar.monthcalendar returns weeks where each week is 7 ints;
        # 0 means the day is outside this month.
        cal = calendar.monthcalendar(year, month)
        weeks = []
        for week in cal:
            week_days = []
            for day_num in week:
                if day_num == 0:
                    week_days.append({
                        "day": 0,
                        "in_month": False,
                        "iso_date": "",
                        "events": [],
                    })
                else:
                    d = datetime.date(year, month, day_num)
                    week_days.append({
                        "day": day_num,
                        "in_month": True,
                        "iso_date": d.isoformat(),
                        "is_today": d == today,
                        "events": event_by_date.get(d, []),
                    })
            weeks.append(week_days)

        months.append({
            "year": year,
            "month": month,
            "name": month_name,
            "weeks": weeks,
        })

        # Advance to next month
        if month == 12:
            cur_month = datetime.date(year + 1, 1, 1)
        else:
            cur_month = datetime.date(year, month + 1, 1)

    return months


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
    if params.get("view") and params["view"] != "card":
        query_params.append(("view", params["view"]))

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

    filters, (activities, page_info) = await asyncio.gather(
        filters_task, search_task
    )

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
            meeting_dates = await activities_service.get_meeting_dates_batch(activity_ids)
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
