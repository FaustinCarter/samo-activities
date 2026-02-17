"""Unit tests for Pydantic models in app/models/."""

import pytest
from pydantic import ValidationError

from app.models.activity import (
    ActionLink,
    ActivityDetail,
    ActivityItem,
    ActivityPattern,
    ActivitySearchPattern,
    ButtonStatus,
    EstimatedPrice,
    FilterOption,
    MeetingAndRegistrationDates,
    PatternDate,
    PriceDetail,
    PriceInfo,
)
from app.models.common import PageInfo


class TestActivityItem:
    """Tests for the ActivityItem model."""

    def test_minimal_activity(self):
        """Create activity with only required fields."""
        activity = ActivityItem(id=123)
        assert activity.id == 123
        assert activity.name == ""
        assert activity.total_open is None

    def test_full_activity(self):
        """Create activity with all fields."""
        activity = ActivityItem(
            id=123,
            name="Swim Lessons",
            desc="Learn to swim",
            number="1234.567",
            date_range_start="2026-03-15",
            date_range_end="2026-04-15",
            location=ActionLink(label="Pool"),
            ages="5-10",
            total_open=5,
            already_enrolled=15,
            fee=ActionLink(href="/fees", label="$50"),
            action_link=ActionLink(href="/enroll", label="Enroll"),
            detail_url="/activity/123",
        )
        assert activity.name == "Swim Lessons"
        assert activity.total_open == 5
        assert activity.location.label == "Pool"

    def test_missing_required_id(self):
        """id is required."""
        with pytest.raises(ValidationError):
            ActivityItem()  # type: ignore


class TestActionLink:
    """Tests for the ActionLink model."""

    def test_defaults(self):
        """All fields have defaults."""
        link = ActionLink()
        assert link.href == ""
        assert link.label == ""
        assert link.type == 0
        assert link.unit == ""

    def test_with_values(self):
        """Set all fields."""
        link = ActionLink(href="/test", label="Test", type=1, unit="each")
        assert link.href == "/test"
        assert link.label == "Test"


class TestActivityPattern:
    """Tests for the ActivityPattern model."""

    def test_defaults(self):
        """All fields have defaults."""
        pattern = ActivityPattern()
        assert pattern.beginning_date == ""
        assert pattern.ending_date == ""
        assert pattern.pattern_dates == []
        assert pattern.exception_dates == []

    def test_with_pattern_dates(self):
        """Create pattern with pattern dates."""
        pattern = ActivityPattern(
            beginning_date="2026-03-01",
            ending_date="2026-03-31",
            pattern_dates=[
                PatternDate(
                    weekdays="Mon, Wed", starting_time="09:00", ending_time="10:00"
                )
            ],
        )
        assert len(pattern.pattern_dates) == 1
        assert pattern.pattern_dates[0].weekdays == "Mon, Wed"


class TestPatternDate:
    """Tests for the PatternDate model."""

    def test_defaults(self):
        """All fields have defaults."""
        pd = PatternDate()
        assert pd.weekdays == ""
        assert pd.starting_time == ""
        assert pd.ending_time == ""

    def test_with_values(self):
        """Set all fields."""
        pd = PatternDate(
            weekdays="Tue, Thu",
            starting_time="14:00:00",
            ending_time="15:30:00",
        )
        assert pd.weekdays == "Tue, Thu"
        assert pd.starting_time == "14:00:00"


class TestMeetingAndRegistrationDates:
    """Tests for the MeetingAndRegistrationDates model."""

    def test_minimal(self):
        """Create with only required fields."""
        meeting = MeetingAndRegistrationDates(activity_id=123)
        assert meeting.activity_id == 123
        assert meeting.no_meeting_dates is False
        assert meeting.activity_patterns == []

    def test_with_patterns(self):
        """Create with activity patterns."""
        meeting = MeetingAndRegistrationDates(
            activity_id=123,
            activity_patterns=[
                ActivityPattern(
                    beginning_date="2026-03-01",
                    ending_date="2026-03-31",
                )
            ],
        )
        assert len(meeting.activity_patterns) == 1


class TestActivityDetail:
    """Tests for the ActivityDetail model."""

    def test_minimal(self):
        """Create with only required fields."""
        detail = ActivityDetail(activity_id=123)
        assert detail.activity_id == 123
        assert detail.activity_name == ""
        assert detail.facilities == []
        assert detail.instructors == []

    def test_full_detail(self):
        """Create with all fields."""
        detail = ActivityDetail(
            activity_id=123,
            activity_name="Yoga Class",
            activity_number="2345.678",
            activity_type="Class",
            season_name="Spring 2026",
            category="Fitness",
            sub_category="Yoga",
            first_date="2026-03-01",
            last_date="2026-05-31",
            facilities=["Studio A", "Studio B"],
            online_notes="<p>Bring a mat.</p>",
        )
        assert detail.activity_name == "Yoga Class"
        assert len(detail.facilities) == 2


class TestFilterOption:
    """Tests for the FilterOption model."""

    def test_display_name_uses_desc(self):
        """display_name prefers desc over name."""
        opt = FilterOption(id=1, desc="Description", name="Name")
        assert opt.display_name == "Description"

    def test_display_name_falls_back_to_name(self):
        """display_name falls back to name if no desc."""
        opt = FilterOption(id=1, name="Name")
        assert opt.display_name == "Name"

    def test_display_name_falls_back_to_id(self):
        """display_name falls back to id if no desc or name."""
        opt = FilterOption(id=42)
        assert opt.display_name == "42"

    def test_id_can_be_string_or_int(self):
        """id field accepts string or int."""
        opt1 = FilterOption(id=123)
        opt2 = FilterOption(id="abc")
        assert opt1.id == 123
        assert opt2.id == "abc"


class TestEstimatedPrice:
    """Tests for the EstimatedPrice model."""

    def test_defaults(self):
        """All fields have sensible defaults."""
        price = EstimatedPrice()
        assert price.show_price_info_online is True
        assert price.free is False
        assert price.prices == []

    def test_free_activity(self):
        """Free activity has free=True."""
        price = EstimatedPrice(free=True)
        assert price.free is True

    def test_with_price_details(self):
        """Create with price details."""
        price = EstimatedPrice(
            estimate_price="$50.00",
            prices=[
                PriceInfo(
                    list_name="Standard",
                    details=[
                        PriceDetail(price="$50.00", description="Resident"),
                    ],
                )
            ],
        )
        assert price.estimate_price == "$50.00"
        assert len(price.prices) == 1
        assert len(price.prices[0].details) == 1


class TestButtonStatus:
    """Tests for the ButtonStatus model."""

    def test_defaults(self):
        """All fields have defaults."""
        status = ButtonStatus()
        assert status.activity_online_start_time == ""
        assert status.action_link is None
        assert status.time_remaining == 0
        assert status.notification == ""

    def test_with_action_link(self):
        """Create with action link."""
        status = ButtonStatus(
            action_link=ActionLink(href="/enroll", label="Enroll Now"),
            notification="Registration opens soon!",
        )
        assert status.action_link.label == "Enroll Now"
        assert status.notification == "Registration opens soon!"


class TestPageInfo:
    """Tests for the PageInfo model."""

    def test_defaults(self):
        """All fields have sensible defaults."""
        page = PageInfo()
        assert page.page_number == 1
        assert page.total_page == 1
        assert page.total_records == 0
        assert page.total_records_per_page == 20

    def test_with_values(self):
        """Create with specific values."""
        page = PageInfo(
            page_number=3,
            total_page=10,
            total_records=200,
            total_records_per_page=20,
        )
        assert page.page_number == 3
        assert page.total_page == 10


class TestActivitySearchPattern:
    """Tests for the ActivitySearchPattern model."""

    def test_defaults(self):
        """All fields have sensible defaults."""
        pattern = ActivitySearchPattern()
        assert pattern.activity_select_param == 2
        assert pattern.activity_keyword == ""
        assert pattern.center_ids == []
        assert pattern.activity_category_ids == []

    def test_with_filters(self):
        """Create with search filters."""
        pattern = ActivitySearchPattern(
            activity_keyword="swim",
            center_ids=[1, 2],
            activity_category_ids=[10],
            date_after="2026-03-01",
            date_before="2026-06-01",
        )
        assert pattern.activity_keyword == "swim"
        assert pattern.center_ids == [1, 2]
        assert pattern.date_after == "2026-03-01"
