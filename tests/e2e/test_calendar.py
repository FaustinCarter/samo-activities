"""E2E tests for calendar view and popup functionality."""

import re

from playwright.sync_api import Page, expect


class TestCalendarView:
    """Tests for the calendar view display."""

    def test_calendar_loads(self, page: Page, server_url: str):
        """Calendar view loads successfully."""
        page.goto(f"{server_url}/?view=calendar")

        expect(page.locator("#cal-root")).to_be_visible()

    def test_calendar_shows_month_title(self, page: Page, server_url: str):
        """Calendar shows month title."""
        page.goto(f"{server_url}/?view=calendar")

        # Should show at least one month (March 2026 based on our mock data)
        expect(page.locator(".cal-month-title").first).to_be_visible()

    def test_calendar_has_grid_structure(self, page: Page, server_url: str):
        """Calendar has proper grid structure."""
        page.goto(f"{server_url}/?view=calendar")

        # Should have header row with day names
        expect(page.locator(".cal-header-row").first).to_be_visible()

        # Should have week rows
        expect(page.locator(".cal-week-row").first).to_be_visible()

    def test_calendar_shows_day_numbers(self, page: Page, server_url: str):
        """Calendar days show day numbers."""
        page.goto(f"{server_url}/?view=calendar")

        # Should have day numbers visible
        expect(page.locator(".cal-day-num").first).to_be_visible()

    def test_event_pills_displayed(self, page: Page, server_url: str):
        """Event pills are displayed on calendar days."""
        page.goto(f"{server_url}/?view=calendar")

        # Should have at least one event pill
        expect(page.locator(".cal-event-pill").first).to_be_visible()

    def test_event_pills_have_color(self, page: Page, server_url: str):
        """Event pills have background color."""
        page.goto(f"{server_url}/?view=calendar")

        pill = page.locator(".cal-event-pill").first
        # Pills should have inline style with background-color
        expect(pill).to_have_attribute("style", re.compile(r"background-color"))


class TestCalendarPopup:
    """Tests for the calendar popup interaction."""

    def test_popup_hidden_by_default(self, page: Page, server_url: str):
        """Popup is hidden when page loads."""
        page.goto(f"{server_url}/?view=calendar")

        popup = page.locator("#cal-popup")
        expect(popup).to_be_hidden()

    def test_popup_opens_on_pill_click(self, page: Page, server_url: str):
        """Popup opens when clicking an event pill."""
        page.goto(f"{server_url}/?view=calendar")

        # Click first event pill
        page.locator(".cal-event-pill").first.click()

        # Popup should be visible
        popup = page.locator("#cal-popup")
        expect(popup).to_be_visible()

    def test_popup_shows_activity_name(self, page: Page, server_url: str):
        """Popup shows the activity name."""
        page.goto(f"{server_url}/?view=calendar")

        page.locator(".cal-event-pill").first.click()

        popup_content = page.locator("#cal-popup-content")
        expect(popup_content).to_contain_text("Youth Swim Lessons")

    def test_popup_shows_location(self, page: Page, server_url: str):
        """Popup shows location information."""
        page.goto(f"{server_url}/?view=calendar")

        page.locator(".cal-event-pill").first.click()

        popup_content = page.locator("#cal-popup-content")
        expect(popup_content).to_contain_text("Memorial Park Pool")

    def test_popup_shows_time(self, page: Page, server_url: str):
        """Popup shows time information."""
        page.goto(f"{server_url}/?view=calendar")

        page.locator(".cal-event-pill").first.click()

        popup_content = page.locator("#cal-popup-content")
        expect(popup_content).to_contain_text("09:00")

    def test_popup_has_view_details_link(self, page: Page, server_url: str):
        """Popup has a link to view activity details."""
        page.goto(f"{server_url}/?view=calendar")

        page.locator(".cal-event-pill").first.click()

        detail_link = page.locator('#cal-popup-content a:has-text("View details")')
        expect(detail_link).to_be_visible()

    def test_popup_closes_on_close_button(self, page: Page, server_url: str):
        """Popup closes when clicking close button."""
        page.goto(f"{server_url}/?view=calendar")

        # Open popup
        page.locator(".cal-event-pill").first.click()
        expect(page.locator("#cal-popup")).to_be_visible()

        # Click close button
        page.locator("#cal-popup-close").click()

        # Popup should be hidden
        expect(page.locator("#cal-popup")).to_be_hidden()

    def test_popup_closes_on_backdrop_click(self, page: Page, server_url: str):
        """Popup closes when clicking the backdrop."""
        page.goto(f"{server_url}/?view=calendar")

        # Open popup
        page.locator(".cal-event-pill").first.click()
        expect(page.locator("#cal-popup")).to_be_visible()

        # Click backdrop
        page.locator("#cal-popup-backdrop").click()

        # Popup should be hidden
        expect(page.locator("#cal-popup")).to_be_hidden()

    def test_popup_closes_on_escape_key(self, page: Page, server_url: str):
        """Popup closes when pressing Escape key."""
        page.goto(f"{server_url}/?view=calendar")

        # Open popup
        page.locator(".cal-event-pill").first.click()
        expect(page.locator("#cal-popup")).to_be_visible()

        # Press Escape
        page.keyboard.press("Escape")

        # Popup should be hidden
        expect(page.locator("#cal-popup")).to_be_hidden()

    def test_clicking_same_pill_toggles_popup(self, page: Page, server_url: str):
        """Clicking the same pill closes the popup."""
        page.goto(f"{server_url}/?view=calendar")

        pill = page.locator(".cal-event-pill").first

        # First click opens
        pill.click()
        expect(page.locator("#cal-popup")).to_be_visible()

        # Close via the close button (clicking same pill doesn't work due to backdrop)
        page.locator("#cal-popup-close").click()
        expect(page.locator("#cal-popup")).to_be_hidden()


class TestActivityDetailPage:
    """Tests for the activity detail page."""

    def test_detail_page_loads(self, page: Page, server_url: str):
        """Activity detail page loads successfully."""
        page.goto(f"{server_url}/activity/12345")

        expect(page.locator(".detail-page")).to_be_visible()

    def test_detail_shows_activity_name(self, page: Page, server_url: str):
        """Detail page shows activity name."""
        page.goto(f"{server_url}/activity/12345")

        expect(page.locator(".detail-title")).to_contain_text(
            "Youth Swim Lessons - Level 1"
        )

    def test_detail_shows_schedule_section(self, page: Page, server_url: str):
        """Detail page shows schedule section."""
        page.goto(f"{server_url}/activity/12345")

        expect(page.locator("h2:has-text('Schedule')")).to_be_visible()

    def test_detail_shows_pricing_section(self, page: Page, server_url: str):
        """Detail page shows pricing section."""
        page.goto(f"{server_url}/activity/12345")

        expect(page.locator("h2:has-text('Pricing')")).to_be_visible()
        expect(page.locator("text=$50.00")).to_be_visible()

    def test_detail_has_back_button(self, page: Page, server_url: str):
        """Detail page has back navigation."""
        page.goto(f"{server_url}/activity/12345")

        expect(page.locator(".btn-back")).to_be_visible()
        expect(page.locator(".btn-back")).to_contain_text("Back")

    def test_detail_has_enroll_button(self, page: Page, server_url: str):
        """Detail page has enrollment button."""
        page.goto(f"{server_url}/activity/12345")

        enroll_btn = page.locator(".btn-enroll--large")
        expect(enroll_btn).to_be_visible()
        expect(enroll_btn).to_contain_text("Enroll Now")

    def test_navigate_from_card_to_detail(self, page: Page, server_url: str):
        """Clicking activity name navigates to detail page."""
        page.goto(server_url)

        # Click first activity link
        page.locator(".activity-name a").first.click()

        # Should be on detail page
        expect(page).to_have_url(re.compile(r"/activity/12345"))
        expect(page.locator(".detail-page")).to_be_visible()

    def test_navigate_from_calendar_popup_to_detail(self, page: Page, server_url: str):
        """Clicking 'View details' in popup navigates to detail page."""
        page.goto(f"{server_url}/?view=calendar")

        # Open popup
        page.locator(".cal-event-pill").first.click()

        # Click view details link
        page.locator('#cal-popup-content a:has-text("View details")').click()

        # Should be on detail page
        expect(page).to_have_url(re.compile(r"/activity/"))
        expect(page.locator(".detail-page")).to_be_visible()
