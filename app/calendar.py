"""Calendar-building logic for the activity browser.

This module converts activity data and meeting-date patterns into the data
structures consumed by the calendar Jinja2 template.  It has no HTTP or
request-handling concerns.
"""

import calendar
import datetime
import urllib.parse

from app.models import activity as activity_models
from app.models import calendar as calendar_models

# ---------------------------------------------------------------------------
# Presentation constants
# ---------------------------------------------------------------------------

# Palette of 20 distinct colors for activity pills on the calendar.
# Each activity gets a stable color by (index % len(PILL_COLORS)).
# With 20 colors and a default page size of 20, each activity gets a unique color.
PILL_COLORS = [
    "#5a7d8a",  # blue-gray (primary)
    "#3a8a6a",  # seafoam
    "#8a6e5e",  # warm stone
    "#7a6a8a",  # muted plum
    "#4a7a8a",  # ocean
    "#9a6858",  # clay
    "#6a8a5a",  # sage
    "#5a8a7a",  # teal mist
    "#8a7a5a",  # khaki
    "#4a6a7a",  # slate
    "#7a8a6a",  # moss
    "#8a5a6a",  # dusty rose
    "#5a8a8a",  # dark cyan
    "#7a5a5a",  # muted maroon
    "#5a7a6a",  # forest mist
    "#9a7a4a",  # amber
    "#6a5a7a",  # lavender gray
    "#4a8a7a",  # dark seafoam
    "#8a7a6a",  # driftwood
    "#6a7a8a",  # cool slate
]

WEEKDAY_ABBR_MAP: dict[str, int] = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def parse_iso(s: str) -> datetime.date | None:
    """Parse an ISO date string (YYYY-MM-DD) to a date, or *None* on failure."""
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(s[:10])
    except ValueError:
        return None


def parse_weekdays(weekdays_str: str) -> list[int]:
    """Parse a weekdays string like ``"Mon, Wed, Fri"`` into weekday ints.

    Returns a list of integers where 0 = Monday ... 6 = Sunday.
    """
    result = []
    for part in weekdays_str.split(","):
        key = part.strip().lower()[:3]
        if key in WEEKDAY_ABBR_MAP:
            result.append(WEEKDAY_ABBR_MAP[key])
    return result


def expand_pattern_dates(
    pattern: activity_models.ActivityPattern,
) -> set[datetime.date]:
    """Expand an :class:`ActivityPattern` into its individual session dates."""
    start = parse_iso(pattern.beginning_date)
    end = parse_iso(pattern.ending_date)
    if start is None or end is None:
        return set()

    # Collect exception dates
    exception_dates: set[datetime.date] = set()
    for exc in pattern.exception_dates or []:
        if isinstance(exc, str):
            d = parse_iso(exc)
            if d:
                exception_dates.add(d)
        elif isinstance(exc, dict):
            d = parse_iso(exc.get("date", ""))
            if d:
                exception_dates.add(d)

    # Collect all weekday numbers across all pattern_dates entries
    all_weekdays: set[int] = set()
    for pd in pattern.pattern_dates:
        all_weekdays.update(parse_weekdays(pd.weekdays))

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


def activity_meeting_dates(
    activity: activity_models.ActivityItem,
    meeting_info: activity_models.MeetingAndRegistrationDates | None,
) -> set[datetime.date]:
    """Return the full set of individual meeting dates for *activity*.

    Falls back to the activity's ``date_range_start`` when no *meeting_info*
    is available or when the patterns produce no dates.
    """
    if meeting_info is None or meeting_info.no_meeting_dates:
        d = parse_iso(activity.date_range_start)
        return {d} if d else set()

    dates: set[datetime.date] = set()
    for pattern in meeting_info.activity_patterns:
        dates.update(expand_pattern_dates(pattern))

    # If patterns gave us nothing, fall back to start date
    if not dates:
        d = parse_iso(activity.date_range_start)
        if d:
            dates.add(d)

    return dates


# ---------------------------------------------------------------------------
# Calendar builder
# ---------------------------------------------------------------------------


def build_calendar_data(
    activities: list[activity_models.ActivityItem],
    meeting_dates: dict[int, activity_models.MeetingAndRegistrationDates],
    button_statuses: dict[int, activity_models.ButtonStatus] | None = None,
) -> list[calendar_models.CalendarMonth]:
    """Build a list of month dicts for the calendar template.

    Each month has ``year``, ``month``, ``name``, and ``weeks``.
    Each week is a list of 7 :class:`CalendarDay` objects, and each day
    carries a list of :class:`CalendarEvent` objects.
    """
    today = datetime.date.today()

    if not activities:
        return []

    # Map date -> list[event] and track date bounds
    event_by_date: dict[datetime.date, list[calendar_models.CalendarEvent]] = {}
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

        # Prefer button status (has correct enroll/waitlist info) over
        # the search-result action_link which may be empty for waitlisted
        # activities.
        btn = button_statuses.get(activity.id) if button_statuses else None
        btn_link = btn.action_link if btn else None
        if not btn_link or not btn_link.href:
            btn_link = activity.action_link

        event_data = activity.model_dump()
        if btn_link:
            event_data["action_link"] = btn_link
        event = calendar_models.CalendarEvent(
            **event_data,
            color=color,
            starting_time=starting_time,
            ending_time=ending_time,
        )

        all_dates = activity_meeting_dates(activity, meeting_info)

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

    # Determine month range: first month with events through last month
    start_month = earliest_date.replace(day=1)
    end_month = latest_date.replace(day=1)

    months: list[calendar_models.CalendarMonth] = []
    cur_month = start_month
    while cur_month <= end_month:
        year = cur_month.year
        month = cur_month.month
        month_name = cur_month.strftime("%B %Y")

        # calendar.monthcalendar returns weeks where each week is 7 ints;
        # 0 means the day is outside this month.
        cal = calendar.monthcalendar(year, month)
        weeks: list[list[calendar_models.CalendarDay]] = []
        for week in cal:
            week_days: list[calendar_models.CalendarDay] = []
            for day_num in week:
                if day_num == 0:
                    week_days.append(
                        calendar_models.CalendarDay(
                            day=0,
                            in_month=False,
                        )
                    )
                else:
                    d = datetime.date(year, month, day_num)
                    week_days.append(
                        calendar_models.CalendarDay(
                            day=day_num,
                            in_month=True,
                            iso_date=d.isoformat(),
                            is_today=d == today,
                            events=event_by_date.get(d, []),
                        )
                    )
            weeks.append(week_days)

        months.append(
            calendar_models.CalendarMonth(
                year=year,
                month=month,
                name=month_name,
                weeks=weeks,
            )
        )

        # Advance to next month
        if month == 12:
            cur_month = datetime.date(year + 1, 1, 1)
        else:
            cur_month = datetime.date(year, month + 1, 1)

    return months


# ---------------------------------------------------------------------------
# Query string helper
# ---------------------------------------------------------------------------


def build_query_string(params: dict, page: int) -> str:
    """Build a query string from *params* dict with a specific *page* number."""
    query_params = []

    if params.get("q"):
        query_params.append(("q", params["q"]))
    if params.get("date_after"):
        query_params.append(("date_after", params["date_after"]))
    if params.get("date_before"):
        query_params.append(("date_before", params["date_before"]))
    if params.get("time_after"):
        query_params.append(("time_after", params["time_after"]))
    if params.get("time_before"):
        query_params.append(("time_before", params["time_before"]))
    for dow in params.get("days_of_week", []):
        query_params.append(("days_of_week", str(dow)))
    if params.get("min_age") is not None:
        query_params.append(("min_age", str(params["min_age"])))
    if params.get("max_age") is not None:
        query_params.append(("max_age", str(params["max_age"])))
    for cat_id in params.get("category_ids", []):
        query_params.append(("category_ids", str(cat_id)))
    for center_id in params.get("center_ids", []):
        query_params.append(("center_ids", str(center_id)))
    if params.get("wishlist_only"):
        query_params.append(("wishlist_only", "true"))
    if params.get("view") and params["view"] != "card":
        query_params.append(("view", params["view"]))

    query_params.append(("page", str(page)))

    return urllib.parse.urlencode(query_params)
