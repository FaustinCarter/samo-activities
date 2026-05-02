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
    notification: str = ""

    def popup_dict(self, authenticated: bool = False) -> dict:
        """Return a flat dict of fields needed by the calendar popup JS.

        This is the source of truth for the ``eventData`` object shape used by
        ``renderPopup()`` in ``app/static/calendar.js``.  The dict is serialized
        to JSON via ``tojson`` in ``app/templates/partials/calendar.html`` and
        embedded in each pill's ``data-event`` attribute.
        """
        data: dict = {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "location": self.location.label if self.location else "",
            "ages": self.ages,
            "total_open": self.total_open,
            "already_enrolled": self.already_enrolled,
            "action_link_href": self.action_link.href if self.action_link else "",
            "action_link_label": (
                self.action_link.label if self.action_link else "Enroll"
            ),
            "action_link_type": self.action_link.type if self.action_link else 0,
            "notification": self.notification,
            "date_range_start": self.date_range_start,
            "date_range_end": self.date_range_end,
            "starting_time": self.starting_time,
            "ending_time": self.ending_time,
            "number": self.number,
        }
        if authenticated:
            data["wish_list_id"] = self.wish_list_id
        return data


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
