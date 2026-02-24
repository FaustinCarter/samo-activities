"""Integration tests for the service layer with mocked HTTP client."""

import pytest
import respx
from httpx import Response

from app.client import ActiveNetClient, APIError
from app.config import settings
from app.models.activity import (
    ActivityFilterOptions,
    ActivityItem,
    ActivitySearchPattern,
    MeetingAndRegistrationDates,
)
from app.services import activities as activities_service


@pytest.fixture
def api_client():
    """Create a bare ActiveNetClient (no bootstrap needed for mocked calls)."""
    return ActiveNetClient()


class TestGetFilters:
    """Tests for the get_filters service function."""

    @respx.mock
    async def test_returns_filter_options(self, api_client, mock_api_filters_response):
        """get_filters returns ActivityFilterOptions."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )

        result = await activities_service.get_filters(api_client)

        assert isinstance(result, ActivityFilterOptions)
        assert len(result.categories) == 3
        assert result.categories[0].name == "Aquatics"

    @respx.mock
    async def test_handles_empty_filters(self, api_client):
        """get_filters handles empty filter response."""
        empty_response = {
            "headers": {"response_code": "0000"},
            "body": {},
        }
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=empty_response)
        )

        result = await activities_service.get_filters(api_client)

        assert isinstance(result, ActivityFilterOptions)
        assert result.categories == []


class TestSearch:
    """Tests for the search service function."""

    @respx.mock
    async def test_returns_activities_and_page_info(
        self, api_client, mock_api_search_response
    ):
        """search returns list of activities and page info."""
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        pattern = ActivitySearchPattern(activity_keyword="swim")
        activities, page_info = await activities_service.search(api_client, pattern)

        assert len(activities) == 3
        assert isinstance(activities[0], ActivityItem)
        assert activities[0].name == "Youth Swim Lessons - Level 1"
        assert page_info.total_records == 50

    @respx.mock
    async def test_handles_empty_results(self, api_client):
        """search handles no results."""
        empty_response = {
            "headers": {
                "response_code": "0001",
                "page_info": {
                    "page_number": 1,
                    "total_page": 0,
                    "total_records": 0,
                },
            },
            "body": {"activity_items": []},
        }
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=empty_response)
        )

        pattern = ActivitySearchPattern(activity_keyword="nonexistent")
        activities, page_info = await activities_service.search(api_client, pattern)

        assert activities == []
        assert page_info.total_records == 0

    @respx.mock
    async def test_pagination_passed_correctly(
        self, api_client, mock_api_search_response
    ):
        """search passes page_number to API."""
        route = respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        pattern = ActivitySearchPattern()
        await activities_service.search(api_client, pattern, page_number=5)

        # Check that page_info header was set
        assert route.called
        request = route.calls[0].request
        assert "page_info" in request.headers
        assert '"page_number":5' in request.headers["page_info"]


class TestGetMeetingDates:
    """Tests for the get_meeting_dates service function."""

    @respx.mock
    async def test_returns_meeting_dates(
        self, api_client, mock_api_meeting_dates_response
    ):
        """get_meeting_dates returns MeetingAndRegistrationDates."""
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))

        result = await activities_service.get_meeting_dates(api_client, 12345)

        assert isinstance(result, MeetingAndRegistrationDates)
        assert result.activity_id == 12345
        assert len(result.activity_patterns) == 1

    @respx.mock
    async def test_returns_none_on_error(self, api_client):
        """get_meeting_dates returns None on API error."""
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/99999"
        ).mock(return_value=Response(500))

        result = await activities_service.get_meeting_dates(api_client, 99999)

        assert result is None

    @respx.mock
    async def test_returns_none_on_empty_response(self, api_client):
        """get_meeting_dates returns None when no data."""
        empty_response = {
            "headers": {"response_code": "0000"},
            "body": {"meeting_and_registration_dates": {}},
        }
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=empty_response))

        result = await activities_service.get_meeting_dates(api_client, 12345)

        assert result is None


class TestGetMeetingDatesBatch:
    """Tests for the get_meeting_dates_batch service function."""

    @respx.mock
    async def test_returns_dict_of_meeting_dates(
        self, api_client, mock_api_meeting_dates_response
    ):
        """get_meeting_dates_batch returns dict mapping id to meeting dates."""
        respx.get(url__regex=r".*/meetingandregistrationdates/\d+").mock(
            return_value=Response(200, json=mock_api_meeting_dates_response)
        )

        result = await activities_service.get_meeting_dates_batch(
            api_client, [12345, 12346]
        )

        assert isinstance(result, dict)
        # At least one should have been fetched successfully
        assert len(result) >= 1

    @respx.mock
    async def test_empty_list_returns_empty_dict(self, api_client):
        """get_meeting_dates_batch returns empty dict for empty input."""
        result = await activities_service.get_meeting_dates_batch(api_client, [])

        assert result == {}

    @respx.mock
    async def test_handles_partial_failures(
        self, api_client, mock_api_meeting_dates_response
    ):
        """get_meeting_dates_batch handles some requests failing."""
        # First request succeeds, second fails
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/99999"
        ).mock(return_value=Response(500))

        result = await activities_service.get_meeting_dates_batch(
            api_client, [12345, 99999]
        )

        # Should still have the successful one
        assert 12345 in result
        assert 99999 not in result


class TestGetActivityDetail:
    """Tests for the get_activity_detail service function."""

    @respx.mock
    async def test_returns_activity_detail(self, api_client, mock_api_detail_response):
        """get_activity_detail returns ActivityDetail."""
        respx.get(f"{settings.base_url}/activity/detail/12345").mock(
            return_value=Response(200, json=mock_api_detail_response)
        )

        result = await activities_service.get_activity_detail(api_client, 12345)

        assert result is not None
        assert result.activity_id == 12345
        assert result.activity_name == "Youth Swim Lessons - Level 1"

    @respx.mock
    async def test_returns_none_for_missing(self, api_client):
        """get_activity_detail returns None for non-existent activity."""
        empty_response = {
            "headers": {"response_code": "0000"},
            "body": {"detail": {}},
        }
        respx.get(f"{settings.base_url}/activity/detail/99999").mock(
            return_value=Response(200, json=empty_response)
        )

        result = await activities_service.get_activity_detail(api_client, 99999)

        assert result is None


class TestGetActivityPrice:
    """Tests for the get_activity_price service function."""

    @respx.mock
    async def test_returns_estimated_price(self, api_client, mock_api_price_response):
        """get_activity_price returns EstimatedPrice."""
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/12345").mock(
            return_value=Response(200, json=mock_api_price_response)
        )

        result = await activities_service.get_activity_price(api_client, 12345)

        assert result is not None
        assert result.estimate_price == "$50.00"
        assert len(result.prices) == 1


class TestGetButtonStatus:
    """Tests for the get_button_status service function."""

    @respx.mock
    async def test_returns_button_status(
        self, api_client, mock_api_button_status_response
    ):
        """get_button_status returns ButtonStatus."""
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/12345").mock(
            return_value=Response(200, json=mock_api_button_status_response)
        )

        result = await activities_service.get_button_status(api_client, 12345)

        assert result is not None
        assert result.action_link is not None
        assert result.action_link.label == "Enroll Now"


class TestActiveNetClient:
    """Tests for the ActiveNetClient class."""

    @respx.mock
    async def test_get_request(self):
        """Client makes GET requests correctly."""
        client = ActiveNetClient()
        respx.get(f"{settings.base_url}/test").mock(
            return_value=Response(
                200,
                json={"headers": {"response_code": "0000"}, "body": {"data": "test"}},
            )
        )

        result = await client.get("/test")

        assert result["body"]["data"] == "test"

    @respx.mock
    async def test_post_request(self):
        """Client makes POST requests correctly."""
        client = ActiveNetClient()
        respx.post(f"{settings.base_url}/test").mock(
            return_value=Response(
                200,
                json={"headers": {"response_code": "0000"}, "body": {"data": "test"}},
            )
        )

        result = await client.post("/test", json_body={"key": "value"})

        assert result["body"]["data"] == "test"

    @respx.mock
    async def test_raises_api_error_on_bad_response_code(self):
        """Client raises APIError for non-success response codes."""
        client = ActiveNetClient()
        respx.get(f"{settings.base_url}/test").mock(
            return_value=Response(
                200,
                json={
                    "headers": {
                        "response_code": "9999",
                        "response_message": "Something went wrong",
                    },
                    "body": {},
                },
            )
        )

        with pytest.raises(APIError) as exc_info:
            await client.get("/test")

        assert exc_info.value.code == "9999"
        assert "Something went wrong" in str(exc_info.value)

    @respx.mock
    async def test_no_error_on_no_results_code(self):
        """Client does not raise error for 0001 (no results) code."""
        client = ActiveNetClient()
        respx.get(f"{settings.base_url}/test").mock(
            return_value=Response(
                200,
                json={
                    "headers": {
                        "response_code": "0001",
                        "response_message": "No results",
                    },
                    "body": {},
                },
            )
        )

        # Should not raise
        result = await client.get("/test")
        assert result["headers"]["response_code"] == "0001"
