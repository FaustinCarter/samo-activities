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
    number: str = ""  # Activity number, e.g. "1201.101"
    date_range_start: str = ""  # ISO date, e.g. "2026-03-30"
    date_range_end: str = ""  # ISO date, e.g. "2026-04-03"
    location: ActionLink | None = None  # .label holds the facility name
    ages: str = ""  # e.g. "5 - 11y 11m"
    total_open: int | None = None  # Spots still available
    already_enrolled: int | None = None
    fee: ActionLink | None = None  # .href links to fee details page
    action_link: ActionLink | None = None
    detail_url: str = ""
    show_wish_list: bool = False  # True when user is logged in
    wish_list_id: int = 0  # 0 = not on wishlist; >0 = wishlist entry ID


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
    # 7-char bitmask, position 0=Sun .. 6=Sat. Empty string = no filter.
    days_of_week: str = ""
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


class EnrollmentDatetimes(pydantic.BaseModel):
    first_daytime_internet: str | None = None
    first_daytime_internet_nonresidents: str | None = None
    first_daytime_internet_members: str | None = None
    last_daytime_internet: str | None = None
    for_drop_in_activity: bool = False


class MeetingAndRegistrationDates(pydantic.BaseModel):
    activity_id: int
    no_meeting_dates: bool = False
    activity_patterns: list[ActivityPattern] = pydantic.Field(default_factory=list)
    priority_enrollment_datetimes: EnrollmentDatetimes | None = None
    enrollment_datetimes: list[EnrollmentDatetimes] = pydantic.Field(
        default_factory=list
    )


# --- Activity detail from /rest/activity/detail/{id} ---


class Instructor(pydantic.BaseModel):
    id: int = 0
    first_name: str = ""
    last_name: str = ""
    is_primary_instructor: bool = False
    email: str = ""
    bio: str = ""
    notes: str = ""
    avatar: str = ""
    phone: str = ""


class Facility(pydantic.BaseModel):
    id: int = 0
    name: str = ""
    detail_url: str = ""
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    phone: str | None = None
    center_id: int = 0


class Center(pydantic.BaseModel):
    id: int = 0
    name: str = ""
    address1: str = ""
    address2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    phone: str = ""
    latitude: float | None = None
    longitude: float | None = None


class ExtraDetail(pydantic.BaseModel):
    description: str = ""
    description_url: str = ""
    detail_value: str = ""
    thumbnail_url: str = ""
    attachment_url: str = ""
    attachment_name: str = ""
    attachment_type: str = ""
    attachment_size: int = 0


class OtherInfo(pydantic.BaseModel):
    department: str = ""
    education_unit: str = ""
    supervisor: str = ""
    skills: list = pydantic.Field(default_factory=list)
    sessions: int = 0


class ActivityDetail(pydantic.BaseModel):
    activity_id: int
    activity_name: str = ""
    activity_number: str = ""
    activity_type: str = ""
    season_name: str = ""
    term_name: str | None = None
    category: str = ""
    sub_category: str = ""
    first_date: str = ""
    last_date: str = ""
    facilities: list[Facility] = pydantic.Field(default_factory=list)
    instructors: list[Instructor] = pydantic.Field(default_factory=list)
    online_notes: str = ""
    user_notes: str = ""
    catalog_description: str = ""
    location_description: str = ""
    age_description: str = ""
    age_min_year: int = 0
    age_min_month: int = 0
    age_max_year: int = 0
    age_max_month: int = 0
    min_grade: str | None = None
    max_grade: str | None = None
    allowed_gender: str = ""
    other_info: OtherInfo | None = None
    extra_detail: list[ExtraDetail] = pydantic.Field(default_factory=list)
    centers: list[Center] = pydantic.Field(default_factory=list)
    space_status: str = ""
    space_message: str = ""
    allow_drop_in_reg: bool = False
    private_lesson: bool = False
    show_wish_list: bool = False
    wish_list_id: int = 0


# --- Pricing from /rest/activity/detail/estimateprice/{id} ---


class PriceDetail(pydantic.BaseModel):
    price: str = ""
    description: str = ""


class PriceInfo(pydantic.BaseModel):
    list_name: str = ""
    activity_name: str = ""
    details: list[PriceDetail] = pydantic.Field(default_factory=list)


class EstimatedPrice(pydantic.BaseModel):
    show_price_info_online: bool = True
    estimate_price: str = ""
    prices: list[PriceInfo] = pydantic.Field(default_factory=list)
    free: bool = False
    simple_fee: bool = False
    is_package: bool = False


# --- Button status from /rest/activity/detail/buttonstatus/{id} ---


class ButtonStatus(pydantic.BaseModel):
    activity_online_start_time: str = ""
    action_link: ActionLink | None = None
    time_remaining: int = 0
    notification: str = ""
