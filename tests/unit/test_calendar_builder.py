"""Unit tests for calendar building functions in routes/activities.py."""

import datetime


from app.routes.activities import (
    build_calendar_data,
    build_query_string,
    _activity_meeting_dates,
)
from app.models.activity import (
    ActionLink,
    ActivityItem,
    ActivityPattern,
    MeetingAndRegistrationDates,
    PatternDate,
)


class TestBuildQueryString:
    """Tests for the build_query_string function."""

    def test_basic_pagination(self):
        """Build query string with just page number."""
        params = {}
        result = build_query_string(params, 2)
        assert result == "page=2"

    def test_with_search_query(self):
        """Include search query parameter."""
        params = {"q": "swim"}
        result = build_query_string(params, 1)
        assert "q=swim" in result
        assert "page=1" in result

    def test_with_date_filters(self):
        """Include date filter parameters."""
        params = {"date_after": "2026-03-01", "date_before": "2026-04-01"}
        result = build_query_string(params, 1)
        assert "date_after=2026-03-01" in result
        assert "date_before=2026-04-01" in result

    def test_with_category_ids(self):
        """Include multiple category IDs."""
        params = {"category_ids": [1, 2, 3]}
        result = build_query_string(params, 1)
        assert "category_ids=1" in result
        assert "category_ids=2" in result
        assert "category_ids=3" in result

    def test_with_center_ids(self):
        """Include multiple center IDs."""
        params = {"center_ids": [10, 20]}
        result = build_query_string(params, 1)
        assert "center_ids=10" in result
        assert "center_ids=20" in result

    def test_with_show_full_details(self):
        """Include show_full_details flag."""
        params = {"show_full_details": True}
        result = build_query_string(params, 1)
        assert "show_full_details=true" in result

    def test_show_full_details_false_not_included(self):
        """show_full_details=False is not included."""
        params = {"show_full_details": False}
        result = build_query_string(params, 1)
        assert "show_full_details" not in result

    def test_with_calendar_view(self):
        """Include view parameter for calendar."""
        params = {"view": "calendar"}
        result = build_query_string(params, 1)
        assert "view=calendar" in result

    def test_card_view_not_included(self):
        """view=card (default) is not included."""
        params = {"view": "card"}
        result = build_query_string(params, 1)
        assert "view=" not in result

    def test_all_params_combined(self):
        """Combine all parameter types."""
        params = {
            "q": "yoga",
            "date_after": "2026-03-01",
            "date_before": "2026-06-01",
            "category_ids": [2],
            "center_ids": [11],
            "show_full_details": True,
            "view": "calendar",
        }
        result = build_query_string(params, 5)
        assert "q=yoga" in result
        assert "date_after=2026-03-01" in result
        assert "date_before=2026-06-01" in result
        assert "category_ids=2" in result
        assert "center_ids=11" in result
        assert "show_full_details=true" in result
        assert "view=calendar" in result
        assert "page=5" in result


class TestActivityMeetingDates:
    """Tests for the _activity_meeting_dates function."""

    def test_with_valid_meeting_info(self):
        """Extract dates from meeting info patterns."""
        activity = ActivityItem(
            id=1,
            name="Test",
            date_range_start="2026-03-16",
            date_range_end="2026-03-22",
        )
        meeting_info = MeetingAndRegistrationDates(
            activity_id=1,
            no_meeting_dates=False,
            activity_patterns=[
                ActivityPattern(
                    beginning_date="2026-03-16",
                    ending_date="2026-03-22",
                    pattern_dates=[PatternDate(weekdays="Mon, Wed")],
                )
            ],
        )
        result = _activity_meeting_dates(activity, meeting_info)
        expected = {
            datetime.date(2026, 3, 16),
            datetime.date(2026, 3, 18),
        }
        assert result == expected

    def test_no_meeting_dates_flag(self):
        """When no_meeting_dates is True, fall back to start date."""
        activity = ActivityItem(
            id=1,
            name="Test",
            date_range_start="2026-03-16",
        )
        meeting_info = MeetingAndRegistrationDates(
            activity_id=1,
            no_meeting_dates=True,
            activity_patterns=[],
        )
        result = _activity_meeting_dates(activity, meeting_info)
        assert result == {datetime.date(2026, 3, 16)}

    def test_none_meeting_info(self):
        """When meeting_info is None, fall back to start date."""
        activity = ActivityItem(
            id=1,
            name="Test",
            date_range_start="2026-03-16",
        )
        result = _activity_meeting_dates(activity, None)
        assert result == {datetime.date(2026, 3, 16)}

    def test_empty_patterns_fallback(self):
        """When patterns produce no dates, fall back to start date."""
        activity = ActivityItem(
            id=1,
            name="Test",
            date_range_start="2026-03-16",
        )
        meeting_info = MeetingAndRegistrationDates(
            activity_id=1,
            no_meeting_dates=False,
            activity_patterns=[
                ActivityPattern(
                    beginning_date="2026-03-16",
                    ending_date="2026-03-22",
                    pattern_dates=[],  # No weekdays specified
                )
            ],
        )
        result = _activity_meeting_dates(activity, meeting_info)
        assert result == {datetime.date(2026, 3, 16)}

    def test_no_start_date(self):
        """When activity has no start date and no patterns, return empty."""
        activity = ActivityItem(id=1, name="Test")
        result = _activity_meeting_dates(activity, None)
        assert result == set()


class TestBuildCalendarData:
    """Tests for the build_calendar_data function."""

    def test_empty_activities(self):
        """Empty activities list returns empty calendar."""
        result = build_calendar_data([], {})
        assert result == []

    def test_single_activity_single_month(self):
        """Single activity creates one month in calendar."""
        activities = [
            ActivityItem(
                id=1,
                name="Test Activity",
                date_range_start="2026-03-16",
                date_range_end="2026-03-20",
                location=ActionLink(label="Test Location"),
                ages="5-10",
                total_open=5,
            )
        ]
        meeting_dates = {
            1: MeetingAndRegistrationDates(
                activity_id=1,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-16",
                        ending_date="2026-03-20",
                        pattern_dates=[PatternDate(weekdays="Mon, Wed, Fri")],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        assert len(result) == 1
        assert result[0]["year"] == 2026
        assert result[0]["month"] == 3
        assert result[0]["name"] == "March 2026"
        assert "weeks" in result[0]

    def test_multiple_months_spanned(self):
        """Activity spanning months creates multiple month entries."""
        activities = [
            ActivityItem(
                id=1,
                name="Test",
                date_range_start="2026-03-01",
                date_range_end="2026-05-15",
            )
        ]
        meeting_dates = {
            1: MeetingAndRegistrationDates(
                activity_id=1,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-01",
                        ending_date="2026-05-15",
                        pattern_dates=[PatternDate(weekdays="Mon")],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        # Should have March, April, May (all have Mondays within the range)
        assert len(result) == 3
        month_names = [m["name"] for m in result]
        assert "March 2026" in month_names
        assert "April 2026" in month_names
        assert "May 2026" in month_names

    def test_events_placed_on_correct_days(self):
        """Events appear on the correct day cells."""
        activities = [
            ActivityItem(
                id=1,
                name="Monday Class",
                date_range_start="2026-03-16",  # This is a Monday
                date_range_end="2026-03-16",
            )
        ]
        meeting_dates = {
            1: MeetingAndRegistrationDates(
                activity_id=1,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-16",
                        ending_date="2026-03-16",
                        pattern_dates=[PatternDate(weekdays="Mon")],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        # Find March 16 in the calendar
        march = result[0]
        found = False
        for week in march["weeks"]:
            for day in week:
                if day["day"] == 16 and day["in_month"]:
                    assert len(day["events"]) == 1
                    assert day["events"][0]["name"] == "Monday Class"
                    found = True
        assert found, "March 16 should have the event"

    def test_event_contains_required_fields(self):
        """Event dicts contain all required fields for calendar display."""
        activities = [
            ActivityItem(
                id=123,
                name="Test Activity",
                number="1234.567",
                date_range_start="2026-03-16",
                date_range_end="2026-03-16",
                location=ActionLink(label="Test Gym"),
                ages="8-12 years",
                total_open=10,
                action_link=ActionLink(
                    href="https://example.com/enroll", label="Sign Up"
                ),
            )
        ]
        meeting_dates = {
            123: MeetingAndRegistrationDates(
                activity_id=123,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-16",
                        ending_date="2026-03-16",
                        pattern_dates=[
                            PatternDate(
                                weekdays="Mon",
                                starting_time="09:00:00",
                                ending_time="10:00:00",
                            )
                        ],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        march = result[0]
        # Find the day with the event
        event = None
        for week in march["weeks"]:
            for day in week:
                if day.get("events"):
                    event = day["events"][0]
                    break
            if event:
                break

        assert event is not None
        assert event["id"] == 123
        assert event["name"] == "Test Activity"
        assert event["number"] == "1234.567"
        assert event["location"] == "Test Gym"
        assert event["ages"] == "8-12 years"
        assert event["total_open"] == 10
        assert event["action_link_href"] == "https://example.com/enroll"
        assert event["action_link_label"] == "Sign Up"
        assert event["starting_time"] == "09:00"
        assert event["ending_time"] == "10:00"
        assert "color" in event  # Color assigned from PILL_COLORS

    def test_multiple_activities_get_different_colors(self):
        """Different activities get assigned different colors."""
        activities = [
            ActivityItem(id=i, name=f"Activity {i}", date_range_start="2026-03-16")
            for i in range(5)
        ]
        meeting_dates = {
            i: MeetingAndRegistrationDates(
                activity_id=i,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-16",
                        ending_date="2026-03-16",
                        pattern_dates=[PatternDate(weekdays="Mon")],
                    )
                ],
            )
            for i in range(5)
        }
        result = build_calendar_data(activities, meeting_dates)

        march = result[0]
        colors = set()
        for week in march["weeks"]:
            for day in week:
                for event in day.get("events", []):
                    colors.add(event["color"])

        # Should have 5 different colors
        assert len(colors) == 5

    def test_week_structure(self):
        """Each week has exactly 7 days."""
        activities = [ActivityItem(id=1, name="Test", date_range_start="2026-03-16")]
        meeting_dates = {
            1: MeetingAndRegistrationDates(
                activity_id=1,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-16",
                        ending_date="2026-03-16",
                        pattern_dates=[PatternDate(weekdays="Mon")],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        for month in result:
            for week in month["weeks"]:
                assert len(week) == 7

    def test_out_of_month_days_marked(self):
        """Days outside the month are marked with in_month=False."""
        activities = [ActivityItem(id=1, name="Test", date_range_start="2026-03-01")]
        meeting_dates = {
            1: MeetingAndRegistrationDates(
                activity_id=1,
                activity_patterns=[
                    ActivityPattern(
                        beginning_date="2026-03-01",
                        ending_date="2026-03-01",
                        pattern_dates=[PatternDate(weekdays="Sun")],
                    )
                ],
            )
        }
        result = build_calendar_data(activities, meeting_dates)

        march = result[0]
        first_week = march["weeks"][0]

        # March 2026 starts on Sunday, so first day of week (Monday) is out of month
        # Check that at least one day in first week is out of month
        out_of_month_days = [d for d in first_week if not d["in_month"]]
        assert len(out_of_month_days) > 0
