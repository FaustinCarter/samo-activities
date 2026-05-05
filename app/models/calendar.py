"""Pydantic models for the calendar view data structures."""

import pydantic

from app.models import activity as activity_models


class CalendarEvent(activity_models.ActivityItem):
    """A single event on a calendar day.

    Inherits all fields from :class:`ActivityItem` and adds calendar-specific
    presentation fields (color, starting/ending time extracted from patterns).
    """

    color: str = ""
    starting_time: str = ""
    ending_time: str = ""


class CalendarDay(pydantic.BaseModel):
    """A single day cell in the calendar grid."""

    day: int
    in_month: bool
    iso_date: str = ""
    is_today: bool = False
    events: list[CalendarEvent] = pydantic.Field(default_factory=list)


class CalendarMonth(pydantic.BaseModel):
    """A full month in the calendar, containing weeks of days."""

    year: int
    month: int
    name: str
    weeks: list[list[CalendarDay]] = pydantic.Field(default_factory=list)
