import pydantic


class ActionLink(pydantic.BaseModel):
    href: str = ""
    label: str = ""
    type: int = 0
    unit: str = ""


class ActivityItem(pydantic.BaseModel):
    id: int
    name: str = ""
    desc: str = ""
    number: str = ""                  # Activity number, e.g. "1201.101"
    date_range_start: str = ""        # ISO date, e.g. "2026-03-30"
    date_range_end: str = ""          # ISO date, e.g. "2026-04-03"
    location: ActionLink | None = None  # .label holds the facility name
    ages: str = ""                    # e.g. "5 - 11y 11m"
    total_open: int | None = None     # Spots still available
    already_enrolled: int | None = None
    fee: ActionLink | None = None     # .href links to fee details page
    action_link: ActionLink | None = None
    detail_url: str = ""


class ActivityListBody(pydantic.BaseModel):
    activity_items: list[ActivityItem] = pydantic.Field(default_factory=list)


class ActivitySearchPattern(pydantic.BaseModel):
    """Request body for POST /rest/activities/list"""

    activity_select_param: int = 2
    activity_keyword: str = ""
    center_ids: list[int] = pydantic.Field(default_factory=list)
    activity_category_ids: list[int] = pydantic.Field(default_factory=list)
    activity_type_ids: list[int] = pydantic.Field(default_factory=list)
    season_ids: list[int] = pydantic.Field(default_factory=list)
    instructor_ids: list[int] = pydantic.Field(default_factory=list)
    site_ids: list[int] = pydantic.Field(default_factory=list)
    geographic_area_ids: list[int] = pydantic.Field(default_factory=list)
    activity_department_ids: list[int] = pydantic.Field(default_factory=list)
    activity_other_category_ids: list[int] = pydantic.Field(default_factory=list)
    child_season_ids: list[int] = pydantic.Field(default_factory=list)
    skills: list = pydantic.Field(default_factory=list)
    days_of_week: list[int] | None = None
    time_after_str: str = ""
    time_before_str: str = ""
    date_after: str = ""
    date_before: str = ""
    min_age: int | None = None
    max_age: int | None = None
    open_spots: int | None = None
    activity_id: int | None = None
    for_map: bool = False
    custom_price_from: str = ""
    custom_price_to: str = ""


class ActivitySearchRequest(pydantic.BaseModel):
    """Full request body for activity search"""

    activity_search_pattern: ActivitySearchPattern = pydantic.Field(
        default_factory=ActivitySearchPattern
    )
    activity_transfer_pattern: dict = pydantic.Field(default_factory=dict)


# --- Filter options from /rest/activities/filters ---


class FilterOption(pydantic.BaseModel):
    id: str | int
    desc: str = ""
    name: str = ""

    @property
    def display_name(self) -> str:
        return self.desc or self.name or str(self.id)


class ActivityFilterOptions(pydantic.BaseModel):
    instructors: list[FilterOption] = pydantic.Field(default_factory=list)
    centers: list[FilterOption] = pydantic.Field(default_factory=list)
    seasons: list[FilterOption] = pydantic.Field(default_factory=list)
    categories: list[FilterOption] = pydantic.Field(default_factory=list)
    activity_types: list[FilterOption] = pydantic.Field(default_factory=list)
    sites: list[FilterOption] = pydantic.Field(default_factory=list)
    geographic_areas: list[FilterOption] = pydantic.Field(default_factory=list)
    skills: list[FilterOption] = pydantic.Field(default_factory=list)


# --- Meeting dates from /rest/activity/detail/meetingandregistrationdates/{id} ---


class PatternDate(pydantic.BaseModel):
    weekdays: str = ""
    starting_time: str = ""
    ending_time: str = ""


class ActivityPattern(pydantic.BaseModel):
    beginning_date: str = ""
    ending_date: str = ""
    weeks_of_month: str = ""
    exception_dates: list = pydantic.Field(default_factory=list)
    pattern_dates: list[PatternDate] = pydantic.Field(default_factory=list)


class MeetingAndRegistrationDates(pydantic.BaseModel):
    activity_id: int
    no_meeting_dates: bool = False
    activity_patterns: list[ActivityPattern] = pydantic.Field(default_factory=list)
