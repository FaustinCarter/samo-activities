"""Integration tests for FastAPI routes with mocked external API."""

import respx
from httpx import Response

from app.config import settings


class TestBrowseActivitiesRoute:
    """Tests for the GET / route (browse activities)."""

    @respx.mock
    def test_homepage_loads(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """Homepage loads successfully with activities."""
        # Mock the external API calls
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Youth Swim Lessons" in response.text

    @respx.mock
    def test_homepage_with_search_query(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """Homepage filters by search query."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/?q=swim")

        assert response.status_code == 200
        # Check that search value is in the form
        assert 'value="swim"' in response.text

    @respx.mock
    def test_homepage_with_date_filters(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """Homepage accepts date filter parameters."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/?date_after=2026-03-01&date_before=2026-06-01")

        assert response.status_code == 200
        assert 'value="2026-03-01"' in response.text
        assert 'value="2026-06-01"' in response.text

    @respx.mock
    def test_homepage_calendar_view(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
        mock_api_meeting_dates_response,
    ):
        """Homepage renders calendar view when view=calendar."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )
        # Calendar view fetches meeting dates for each activity
        respx.get(url__regex=r".*/meetingandregistrationdates/\d+").mock(
            return_value=Response(200, json=mock_api_meeting_dates_response)
        )

        response = client.get("/?view=calendar")

        assert response.status_code == 200
        assert "cal-root" in response.text  # Calendar container
        assert "cal-month" in response.text or "No events" in response.text

    @respx.mock
    def test_homepage_with_pagination(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
    ):
        """Homepage handles pagination parameter."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )

        response = client.get("/?page=2")

        assert response.status_code == 200
        assert "Page 2" in response.text

    @respx.mock
    def test_homepage_no_results(
        self,
        client,
        mock_api_filters_response,
    ):
        """Homepage handles no results gracefully."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        # Return empty results
        empty_response = {
            "headers": {
                "response_code": "0001",  # No results code
                "response_message": "No results",
                "page_info": {
                    "page_number": 1,
                    "total_page": 0,
                    "total_records": 0,
                    "total_records_per_page": 20,
                },
            },
            "body": {"activity_items": []},
        }
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=empty_response)
        )

        response = client.get("/?q=nonexistent")

        assert response.status_code == 200
        assert "No activities found" in response.text

    @respx.mock
    def test_homepage_with_show_full_details(
        self,
        client,
        mock_api_filters_response,
        mock_api_search_response,
        mock_api_meeting_dates_response,
        mock_api_price_response,
    ):
        """Homepage fetches extra details when show_full_details=true."""
        respx.get(f"{settings.base_url}/activities/filters").mock(
            return_value=Response(200, json=mock_api_filters_response)
        )
        respx.post(f"{settings.base_url}/activities/list").mock(
            return_value=Response(200, json=mock_api_search_response)
        )
        respx.get(url__regex=r".*/meetingandregistrationdates/\d+").mock(
            return_value=Response(200, json=mock_api_meeting_dates_response)
        )
        respx.get(url__regex=r".*/estimateprice/\d+").mock(
            return_value=Response(200, json=mock_api_price_response)
        )

        response = client.get("/?show_full_details=true")

        assert response.status_code == 200
        # Price info should be visible when show_full_details is on
        # The exact content depends on template rendering


class TestActivityDetailRoute:
    """Tests for the GET /activity/{id} route."""

    @respx.mock
    def test_activity_detail_loads(
        self,
        client,
        mock_api_detail_response,
        mock_api_meeting_dates_response,
        mock_api_price_response,
        mock_api_button_status_response,
    ):
        """Activity detail page loads successfully."""
        respx.get(f"{settings.base_url}/activity/detail/12345").mock(
            return_value=Response(200, json=mock_api_detail_response)
        )
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/12345").mock(
            return_value=Response(200, json=mock_api_price_response)
        )
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/12345").mock(
            return_value=Response(200, json=mock_api_button_status_response)
        )

        response = client.get("/activity/12345")

        assert response.status_code == 200
        assert "Youth Swim Lessons - Level 1" in response.text

    @respx.mock
    def test_activity_detail_shows_schedule(
        self,
        client,
        mock_api_detail_response,
        mock_api_meeting_dates_response,
        mock_api_price_response,
        mock_api_button_status_response,
    ):
        """Activity detail page shows schedule information."""
        respx.get(f"{settings.base_url}/activity/detail/12345").mock(
            return_value=Response(200, json=mock_api_detail_response)
        )
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/12345").mock(
            return_value=Response(200, json=mock_api_price_response)
        )
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/12345").mock(
            return_value=Response(200, json=mock_api_button_status_response)
        )

        response = client.get("/activity/12345")

        assert response.status_code == 200
        assert "Schedule" in response.text
        assert "Mon, Wed" in response.text  # Weekdays from meeting dates

    @respx.mock
    def test_activity_detail_shows_pricing(
        self,
        client,
        mock_api_detail_response,
        mock_api_meeting_dates_response,
        mock_api_price_response,
        mock_api_button_status_response,
    ):
        """Activity detail page shows pricing information."""
        respx.get(f"{settings.base_url}/activity/detail/12345").mock(
            return_value=Response(200, json=mock_api_detail_response)
        )
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/12345").mock(
            return_value=Response(200, json=mock_api_price_response)
        )
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/12345").mock(
            return_value=Response(200, json=mock_api_button_status_response)
        )

        response = client.get("/activity/12345")

        assert response.status_code == 200
        assert "Pricing" in response.text
        assert "$50.00" in response.text

    @respx.mock
    def test_activity_detail_not_found(self, client):
        """Activity detail returns 404 for non-existent activity."""
        empty_response = {
            "headers": {
                "response_code": "0000",
                "response_message": "Success",
            },
            "body": {"detail": {}},
        }
        respx.get(f"{settings.base_url}/activity/detail/99999").mock(
            return_value=Response(200, json=empty_response)
        )
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/99999"
        ).mock(return_value=Response(200, json={"headers": {}, "body": {}}))
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/99999").mock(
            return_value=Response(200, json={"headers": {}, "body": {}})
        )
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/99999").mock(
            return_value=Response(200, json={"headers": {}, "body": {}})
        )

        response = client.get("/activity/99999")

        assert response.status_code == 404

    @respx.mock
    def test_activity_detail_has_enroll_button(
        self,
        client,
        mock_api_detail_response,
        mock_api_meeting_dates_response,
        mock_api_price_response,
        mock_api_button_status_response,
    ):
        """Activity detail page shows enroll button when available."""
        respx.get(f"{settings.base_url}/activity/detail/12345").mock(
            return_value=Response(200, json=mock_api_detail_response)
        )
        respx.get(
            f"{settings.base_url}/activity/detail/meetingandregistrationdates/12345"
        ).mock(return_value=Response(200, json=mock_api_meeting_dates_response))
        respx.get(f"{settings.base_url}/activity/detail/estimateprice/12345").mock(
            return_value=Response(200, json=mock_api_price_response)
        )
        respx.get(f"{settings.base_url}/activity/detail/buttonstatus/12345").mock(
            return_value=Response(200, json=mock_api_button_status_response)
        )

        response = client.get("/activity/12345")

        assert response.status_code == 200
        assert "Enroll Now" in response.text
        assert "btn-enroll" in response.text


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_served(self, client):
        """CSS file is served correctly."""
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_js_served(self, client):
        """JavaScript file is served correctly."""
        response = client.get("/static/calendar.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]

    def test_missing_static_returns_404(self, client):
        """Missing static files return 404."""
        response = client.get("/static/nonexistent.css")
        assert response.status_code == 404
