"""Shared test fixtures for the Santa Monica Activities app."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.activity import (
    ActionLink,
    ActivityDetail,
    ActivityFilterOptions,
    ActivityItem,
    ActivityPattern,
    ButtonStatus,
    EnrollmentDatetimes,
    EstimatedPrice,
    FilterOption,
    MeetingAndRegistrationDates,
    PatternDate,
    PriceDetail,
    PriceInfo,
)
from app.models.common import PageInfo


@pytest.fixture
def app():
    """Create a fresh FastAPI application for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app.

    ``ActiveNetClient.bootstrap`` is patched to a no-op so the session
    middleware can create anonymous sessions without hitting the real
    ActiveNet sign-in page.
    """
    with patch(
        "app.client.ActiveNetClient.bootstrap",
        new_callable=AsyncMock,
    ):
        yield TestClient(app)


@pytest.fixture
def sample_activity_item() -> ActivityItem:
    """A single sample activity for testing."""
    return ActivityItem(
        id=12345,
        name="Youth Swim Lessons - Level 1",
        desc="Learn to swim basics",
        number="1201.101",
        date_range_start="2026-03-15",
        date_range_end="2026-04-15",
        location=ActionLink(href="/facility/1", label="Memorial Park Pool"),
        ages="5 - 8 years",
        total_open=5,
        already_enrolled=10,
        fee=ActionLink(href="/fees/12345", label="$50.00"),
        action_link=ActionLink(
            href="https://anc.apm.activecommunities.com/enroll/12345",
            label="Enroll Now",
        ),
        detail_url="/activity/12345",
    )


@pytest.fixture
def sample_activities(sample_activity_item) -> list[ActivityItem]:
    """A list of sample activities for testing."""
    return [
        sample_activity_item,
        ActivityItem(
            id=12346,
            name="Adult Yoga",
            number="2301.201",
            date_range_start="2026-03-20",
            date_range_end="2026-05-20",
            location=ActionLink(label="Community Center"),
            ages="18+ years",
            total_open=12,
        ),
        ActivityItem(
            id=12347,
            name="Kids Basketball Camp",
            number="3401.101",
            date_range_start="2026-06-01",
            date_range_end="2026-06-30",
            location=ActionLink(label="Lincoln Middle School Gym"),
            ages="8 - 12 years",
            total_open=0,
        ),
    ]


@pytest.fixture
def sample_meeting_dates() -> MeetingAndRegistrationDates:
    """Sample meeting dates for an activity."""
    return MeetingAndRegistrationDates(
        activity_id=12345,
        no_meeting_dates=False,
        activity_patterns=[
            ActivityPattern(
                beginning_date="2026-03-15",
                ending_date="2026-04-15",
                weeks_of_month="",
                exception_dates=[],
                pattern_dates=[
                    PatternDate(
                        weekdays="Mon, Wed",
                        starting_time="09:00:00",
                        ending_time="10:00:00",
                    ),
                ],
            ),
        ],
        priority_enrollment_datetimes=EnrollmentDatetimes(
            first_daytime_internet="2026-02-01T08:00:00",
        ),
    )


@pytest.fixture
def sample_activity_detail() -> ActivityDetail:
    """Sample activity detail for testing."""
    return ActivityDetail(
        activity_id=12345,
        activity_name="Youth Swim Lessons - Level 1",
        activity_number="1201.101",
        activity_type="Class",
        season_name="Spring 2026",
        category="Aquatics",
        sub_category="Swim Lessons",
        first_date="2026-03-15",
        last_date="2026-04-15",
        facilities=["Memorial Park Pool"],
        online_notes="<p>Bring your own towel and goggles.</p>",
    )


@pytest.fixture
def sample_price() -> EstimatedPrice:
    """Sample pricing information."""
    return EstimatedPrice(
        show_price_info_online=True,
        estimate_price="$50.00",
        prices=[
            PriceInfo(
                list_name="Standard",
                activity_name="Youth Swim Lessons",
                details=[
                    PriceDetail(price="$50.00", description="Resident"),
                    PriceDetail(price="$75.00", description="Non-Resident"),
                ],
            ),
        ],
        free=False,
        simple_fee=False,
        is_package=False,
    )


@pytest.fixture
def sample_button_status() -> ButtonStatus:
    """Sample button status for enrollment."""
    return ButtonStatus(
        activity_online_start_time="2026-02-01T08:00:00",
        action_link=ActionLink(
            href="https://anc.apm.activecommunities.com/enroll/12345",
            label="Enroll Now",
        ),
        time_remaining=0,
        notification="",
    )


@pytest.fixture
def sample_filters() -> ActivityFilterOptions:
    """Sample filter options for the search UI."""
    return ActivityFilterOptions(
        categories=[
            FilterOption(id=1, name="Aquatics"),
            FilterOption(id=2, name="Fitness"),
            FilterOption(id=3, name="Sports"),
        ],
        centers=[
            FilterOption(id=10, name="Memorial Park"),
            FilterOption(id=11, name="Community Center"),
        ],
        instructors=[],
        seasons=[FilterOption(id=100, name="Spring 2026")],
        activity_types=[],
        sites=[],
        geographic_areas=[],
        skills=[],
    )


@pytest.fixture
def sample_page_info() -> PageInfo:
    """Sample pagination info."""
    return PageInfo(
        order_by="",
        order_option="ASC",
        total_page=3,
        total_records_per_page=20,
        total_records=50,
        page_number=1,
    )


@pytest.fixture
def mock_api_search_response(sample_activities, sample_page_info) -> dict:
    """Mock response from the activities/list API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
            "page_info": sample_page_info.model_dump(),
        },
        "body": {
            "activity_items": [a.model_dump() for a in sample_activities],
        },
    }


@pytest.fixture
def mock_api_filters_response(sample_filters) -> dict:
    """Mock response from the activities/filters API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
        },
        "body": sample_filters.model_dump(),
    }


@pytest.fixture
def mock_api_detail_response(sample_activity_detail) -> dict:
    """Mock response from the activity/detail/{id} API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
        },
        "body": {
            "detail": sample_activity_detail.model_dump(),
        },
    }


@pytest.fixture
def mock_api_meeting_dates_response(sample_meeting_dates) -> dict:
    """Mock response from the meetingandregistrationdates API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
        },
        "body": {
            "meeting_and_registration_dates": sample_meeting_dates.model_dump(),
        },
    }


@pytest.fixture
def mock_api_price_response(sample_price) -> dict:
    """Mock response from the estimateprice API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
        },
        "body": {
            "estimateprice": sample_price.model_dump(),
        },
    }


@pytest.fixture
def mock_api_button_status_response(sample_button_status) -> dict:
    """Mock response from the buttonstatus API endpoint."""
    return {
        "headers": {
            "response_code": "0000",
            "response_message": "Success",
        },
        "body": {
            "button_status": sample_button_status.model_dump(),
        },
    }
