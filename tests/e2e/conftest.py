"""E2E test fixtures for Playwright browser tests."""

import socket
import threading
import time
from unittest.mock import patch

import pytest
import uvicorn

from app.main import create_app
from app.models.activity import (
    ActionLink,
    ActivityDetail,
    ActivityFilterOptions,
    ActivityItem,
    ActivityPattern,
    ButtonStatus,
    EstimatedPrice,
    FilterOption,
    MeetingAndRegistrationDates,
    PatternDate,
    PriceDetail,
    PriceInfo,
)
from app.models.common import PageInfo


def find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerThread(threading.Thread):
    """Thread that runs the FastAPI app with uvicorn."""

    def __init__(self, app, host: str = "127.0.0.1", port: int = 0):
        super().__init__(daemon=True)
        self.app = app
        self.host = host
        self.port = port or find_free_port()
        self.server = None

    def run(self):
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="module")
def mock_filters():
    """Mock filter options."""
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
    )


@pytest.fixture(scope="module")
def mock_activities():
    """Mock activities list."""
    return [
        ActivityItem(
            id=12345,
            name="Youth Swim Lessons - Level 1",
            number="1201.101",
            date_range_start="2026-03-15",
            date_range_end="2026-04-15",
            location=ActionLink(label="Memorial Park Pool"),
            ages="5 - 8 years",
            total_open=5,
            action_link=ActionLink(
                href="https://example.com/enroll/12345",
                label="Enroll Now",
            ),
        ),
        ActivityItem(
            id=12346,
            name="Adult Yoga Class",
            number="2301.201",
            date_range_start="2026-03-20",
            date_range_end="2026-05-20",
            location=ActionLink(label="Community Center"),
            ages="18+ years",
            total_open=12,
            action_link=ActionLink(
                href="https://example.com/enroll/12346",
                label="Enroll Now",
            ),
        ),
        ActivityItem(
            id=12347,
            name="Kids Basketball Camp",
            number="3401.101",
            date_range_start="2026-06-01",
            date_range_end="2026-06-30",
            location=ActionLink(label="Lincoln Gym"),
            ages="8 - 12 years",
            total_open=0,
        ),
    ]


@pytest.fixture(scope="module")
def mock_page_info():
    """Mock page info."""
    return PageInfo(
        page_number=1,
        total_page=2,
        total_records=25,
        total_records_per_page=20,
    )


@pytest.fixture(scope="module")
def mock_meeting_dates():
    """Mock meeting dates."""
    return MeetingAndRegistrationDates(
        activity_id=12345,
        no_meeting_dates=False,
        activity_patterns=[
            ActivityPattern(
                beginning_date="2026-03-15",
                ending_date="2026-04-15",
                pattern_dates=[
                    PatternDate(
                        weekdays="Mon, Wed",
                        starting_time="09:00:00",
                        ending_time="10:00:00",
                    )
                ],
            )
        ],
    )


@pytest.fixture(scope="module")
def mock_detail():
    """Mock activity detail."""
    return ActivityDetail(
        activity_id=12345,
        activity_name="Youth Swim Lessons - Level 1",
        activity_number="1201.101",
        activity_type="Class",
        season_name="Spring 2026",
        category="Aquatics",
        first_date="2026-03-15",
        last_date="2026-04-15",
        facilities=["Memorial Park Pool"],
        online_notes="<p>Bring your own towel.</p>",
    )


@pytest.fixture(scope="module")
def mock_price():
    """Mock price info."""
    return EstimatedPrice(
        estimate_price="$50.00",
        prices=[
            PriceInfo(
                list_name="Standard",
                details=[PriceDetail(price="$50.00", description="Resident")],
            )
        ],
    )


@pytest.fixture(scope="module")
def mock_button_status():
    """Mock button status."""
    return ButtonStatus(
        action_link=ActionLink(
            href="https://example.com/enroll/12345",
            label="Enroll Now",
        )
    )


@pytest.fixture(scope="module")
def live_server(
    mock_filters,
    mock_activities,
    mock_page_info,
    mock_meeting_dates,
    mock_detail,
    mock_price,
    mock_button_status,
):
    """
    Start a live server for E2E tests with mocked service layer.

    Scoped to module to avoid conflicts with other test modules.
    """

    # Create mock functions
    async def mock_get_filters_fn(*args, **kwargs):
        return mock_filters

    async def mock_search_fn(*args, **kwargs):
        return (mock_activities, mock_page_info)

    async def mock_get_meeting_dates_fn(activity_id, *args, **kwargs):
        return mock_meeting_dates

    async def mock_get_meeting_dates_batch_fn(activity_ids, *args, **kwargs):
        return {aid: mock_meeting_dates for aid in activity_ids}

    async def mock_get_activity_detail_fn(activity_id, *args, **kwargs):
        if activity_id == 12345:
            return mock_detail
        return None

    async def mock_get_activity_price_fn(activity_id, *args, **kwargs):
        return mock_price

    async def mock_get_prices_batch_fn(activity_ids, *args, **kwargs):
        return {aid: mock_price for aid in activity_ids}

    async def mock_get_button_status_fn(activity_id, *args, **kwargs):
        return mock_button_status

    # Patch at the routes module level where these functions are imported
    patches = [
        patch(
            "app.routes.activities.activities_service.get_filters", mock_get_filters_fn
        ),
        patch("app.routes.activities.activities_service.search", mock_search_fn),
        patch(
            "app.routes.activities.activities_service.get_meeting_dates",
            mock_get_meeting_dates_fn,
        ),
        patch(
            "app.routes.activities.activities_service.get_meeting_dates_batch",
            mock_get_meeting_dates_batch_fn,
        ),
        patch(
            "app.routes.activities.activities_service.get_activity_detail",
            mock_get_activity_detail_fn,
        ),
        patch(
            "app.routes.activities.activities_service.get_activity_price",
            mock_get_activity_price_fn,
        ),
        patch(
            "app.routes.activities.activities_service.get_prices_batch",
            mock_get_prices_batch_fn,
        ),
        patch(
            "app.routes.activities.activities_service.get_button_status",
            mock_get_button_status_fn,
        ),
    ]

    # Start all patches
    for p in patches:
        p.start()

    try:
        app = create_app()
        port = find_free_port()
        server = ServerThread(app, port=port)
        server.start()

        # Wait for server to start
        time.sleep(0.5)

        yield f"http://127.0.0.1:{port}"

        server.stop()
        time.sleep(0.2)  # Allow server to fully stop
    finally:
        # Stop all patches
        for p in patches:
            p.stop()


@pytest.fixture(scope="module")
def server_url(live_server):
    """Return the base URL of the live server."""
    return live_server
