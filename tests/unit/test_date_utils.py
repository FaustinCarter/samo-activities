"""Unit tests for date parsing and utility functions in app/calendar.py."""

import datetime


from app.calendar import (
    parse_iso,
    parse_weekdays,
    expand_pattern_dates,
)
from app.models.activity import ActivityPattern, PatternDate


class TestParseIso:
    """Tests for the parse_iso function."""

    def test_valid_date(self):
        """Parse a valid ISO date string."""
        result = parse_iso("2026-03-15")
        assert result == datetime.date(2026, 3, 15)

    def test_empty_string(self):
        """Empty string returns None."""
        assert parse_iso("") is None

    def test_none_like_empty(self):
        """Falsy values return None."""
        assert parse_iso(None) is None  # type: ignore

    def test_invalid_format(self):
        """Invalid date format returns None."""
        assert parse_iso("03-15-2026") is None
        assert parse_iso("not-a-date") is None
        assert parse_iso("2026/03/15") is None

    def test_truncates_to_ten_chars(self):
        """Datetime strings are truncated to date portion."""
        result = parse_iso("2026-03-15T10:30:00")
        assert result == datetime.date(2026, 3, 15)

    def test_invalid_date_values(self):
        """Invalid date values (e.g., month 13) return None."""
        assert parse_iso("2026-13-15") is None
        assert parse_iso("2026-02-30") is None


class TestParseWeekdays:
    """Tests for the parse_weekdays function."""

    def test_single_day(self):
        """Parse a single weekday."""
        assert parse_weekdays("Mon") == [0]
        assert parse_weekdays("Fri") == [4]
        assert parse_weekdays("Sun") == [6]

    def test_multiple_days(self):
        """Parse multiple weekdays separated by commas."""
        result = parse_weekdays("Mon, Wed, Fri")
        assert result == [0, 2, 4]

    def test_all_days(self):
        """Parse all weekdays."""
        result = parse_weekdays("Mon, Tue, Wed, Thu, Fri, Sat, Sun")
        assert result == [0, 1, 2, 3, 4, 5, 6]

    def test_case_insensitive(self):
        """Parsing is case-insensitive."""
        assert parse_weekdays("MON") == [0]
        assert parse_weekdays("mon") == [0]
        assert parse_weekdays("MoN") == [0]

    def test_full_day_names(self):
        """Full day names are parsed (uses first 3 chars)."""
        result = parse_weekdays("Monday, Wednesday")
        assert result == [0, 2]

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert parse_weekdays("") == []

    def test_invalid_days(self):
        """Invalid day names are ignored."""
        result = parse_weekdays("Mon, Invalid, Wed")
        assert result == [0, 2]

    def test_extra_whitespace(self):
        """Extra whitespace is handled."""
        result = parse_weekdays("  Mon  ,  Wed  ")
        assert result == [0, 2]


class TestExpandPatternDates:
    """Tests for the expand_pattern_dates function."""

    def test_single_week_pattern(self):
        """Expand a simple one-week pattern on Mon/Wed."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",  # Monday
            ending_date="2026-03-22",  # Sunday
            pattern_dates=[PatternDate(weekdays="Mon, Wed")],
        )
        result = expand_pattern_dates(pattern)
        expected = {
            datetime.date(2026, 3, 16),  # Monday
            datetime.date(2026, 3, 18),  # Wednesday
        }
        assert result == expected

    def test_multi_week_pattern(self):
        """Expand a pattern spanning multiple weeks."""
        pattern = ActivityPattern(
            beginning_date="2026-03-02",  # Monday
            ending_date="2026-03-15",  # Sunday (2 full weeks)
            pattern_dates=[PatternDate(weekdays="Tue, Thu")],
        )
        result = expand_pattern_dates(pattern)
        # Week 1: Tue 3/3, Thu 3/5
        # Week 2: Tue 3/10, Thu 3/12
        expected = {
            datetime.date(2026, 3, 3),
            datetime.date(2026, 3, 5),
            datetime.date(2026, 3, 10),
            datetime.date(2026, 3, 12),
        }
        assert result == expected

    def test_exception_dates_as_strings(self):
        """Exception dates (as strings) are excluded."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",
            ending_date="2026-03-22",
            pattern_dates=[PatternDate(weekdays="Mon, Wed")],
            exception_dates=["2026-03-18"],  # Exclude Wednesday
        )
        result = expand_pattern_dates(pattern)
        expected = {datetime.date(2026, 3, 16)}  # Only Monday
        assert result == expected

    def test_exception_dates_as_dicts(self):
        """Exception dates (as dicts with 'date' key) are excluded."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",
            ending_date="2026-03-22",
            pattern_dates=[PatternDate(weekdays="Mon, Wed")],
            exception_dates=[{"date": "2026-03-16"}],  # Exclude Monday
        )
        result = expand_pattern_dates(pattern)
        expected = {datetime.date(2026, 3, 18)}  # Only Wednesday
        assert result == expected

    def test_weeks_of_month_filter(self):
        """weeks_of_month limits to specific week occurrences."""
        # March 2026: 1st Monday is 3/2, 2nd is 3/9, 3rd is 3/16, 4th is 3/23
        pattern = ActivityPattern(
            beginning_date="2026-03-01",
            ending_date="2026-03-31",
            weeks_of_month="1, 3",  # 1st and 3rd Monday of month
            pattern_dates=[PatternDate(weekdays="Mon")],
        )
        result = expand_pattern_dates(pattern)
        expected = {
            datetime.date(2026, 3, 2),  # 1st Monday
            datetime.date(2026, 3, 16),  # 3rd Monday
        }
        assert result == expected

    def test_missing_start_date(self):
        """Missing start date returns empty set."""
        pattern = ActivityPattern(
            beginning_date="",
            ending_date="2026-03-22",
            pattern_dates=[PatternDate(weekdays="Mon")],
        )
        assert expand_pattern_dates(pattern) == set()

    def test_missing_end_date(self):
        """Missing end date returns empty set."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",
            ending_date="",
            pattern_dates=[PatternDate(weekdays="Mon")],
        )
        assert expand_pattern_dates(pattern) == set()

    def test_empty_pattern_dates(self):
        """No pattern_dates means no weekdays, returns empty set."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",
            ending_date="2026-03-22",
            pattern_dates=[],
        )
        assert expand_pattern_dates(pattern) == set()

    def test_multiple_pattern_dates(self):
        """Multiple pattern_dates entries are combined."""
        pattern = ActivityPattern(
            beginning_date="2026-03-16",
            ending_date="2026-03-22",
            pattern_dates=[
                PatternDate(weekdays="Mon"),
                PatternDate(weekdays="Fri"),
            ],
        )
        result = expand_pattern_dates(pattern)
        expected = {
            datetime.date(2026, 3, 16),  # Monday
            datetime.date(2026, 3, 20),  # Friday
        }
        assert result == expected
