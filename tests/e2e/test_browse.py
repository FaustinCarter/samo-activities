"""E2E tests for browsing activities."""

import re

from playwright.sync_api import Page, expect


class TestHomepage:
    """Tests for the homepage / activity browser."""

    def test_homepage_loads(self, page: Page, server_url: str):
        """Homepage loads and shows activities."""
        page.goto(server_url)

        # Page should have loaded
        expect(page).to_have_title("Santa Monica Activities")

        # Should show activity cards
        expect(page.locator(".activity-card")).to_have_count(3)

    def test_activities_display_name(self, page: Page, server_url: str):
        """Activity cards show activity names."""
        page.goto(server_url)

        # Check first activity name is visible
        expect(page.locator(".activity-name").first).to_contain_text(
            "Youth Swim Lessons"
        )

    def test_activities_display_location(self, page: Page, server_url: str):
        """Activity cards show location."""
        page.goto(server_url)

        expect(page.locator(".activity-location").first).to_contain_text(
            "Memorial Park Pool"
        )

    def test_activities_display_ages(self, page: Page, server_url: str):
        """Activity cards show age range."""
        page.goto(server_url)

        expect(page.locator(".activity-age").first).to_contain_text("5 - 8 years")

    def test_activities_display_spots(self, page: Page, server_url: str):
        """Activity cards show available spots."""
        page.goto(server_url)

        expect(page.locator(".activity-spots").first).to_contain_text("5 spots open")

    def test_results_count_shown(self, page: Page, server_url: str):
        """Results count is displayed."""
        page.goto(server_url)

        expect(page.locator(".results-count")).to_contain_text("25 activities")


class TestSearchFilter:
    """Tests for the search/filter functionality."""

    def test_search_form_exists(self, page: Page, server_url: str):
        """Search form is present on the page."""
        page.goto(server_url)

        expect(page.locator("#filter-form")).to_be_visible()
        expect(page.locator('input[name="q"]')).to_be_visible()

    def test_search_input_accepts_text(self, page: Page, server_url: str):
        """Search input can be typed into."""
        page.goto(server_url)

        search_input = page.locator('input[name="q"]')
        search_input.fill("swim")

        expect(search_input).to_have_value("swim")

    def test_date_filters_exist(self, page: Page, server_url: str):
        """Date filter inputs are present."""
        page.goto(server_url)

        expect(page.locator('input[name="date_after"]')).to_be_visible()
        expect(page.locator('input[name="date_before"]')).to_be_visible()

    def test_category_select_exists(self, page: Page, server_url: str):
        """Category filter dropdown is present."""
        page.goto(server_url)

        expect(page.locator('select[name="category_ids"]')).to_be_visible()

    def test_location_select_exists(self, page: Page, server_url: str):
        """Location filter dropdown is present."""
        page.goto(server_url)

        expect(page.locator('select[name="center_ids"]')).to_be_visible()

    def test_search_button_exists(self, page: Page, server_url: str):
        """Search button is present."""
        page.goto(server_url)

        expect(page.locator('button[type="submit"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_contain_text("Search")


class TestViewToggle:
    """Tests for the card/calendar view toggle."""

    def test_view_toggle_exists(self, page: Page, server_url: str):
        """View toggle buttons are present."""
        page.goto(server_url)

        expect(page.locator(".view-toggle")).to_be_visible()
        expect(page.locator('[data-view="card"]')).to_be_visible()
        expect(page.locator('[data-view="calendar"]')).to_be_visible()

    def test_card_view_active_by_default(self, page: Page, server_url: str):
        """Card view is active by default."""
        page.goto(server_url)

        card_btn = page.locator('[data-view="card"]')
        expect(card_btn).to_have_class(re.compile(r"active"))

    def test_switch_to_calendar_view(self, page: Page, server_url: str):
        """Clicking calendar button switches to calendar view."""
        page.goto(server_url)

        # Click calendar view button
        page.locator('[data-view="calendar"]').click()

        # Should navigate to calendar view
        expect(page).to_have_url(re.compile(r"view=calendar"))

        # Calendar container should be visible
        expect(page.locator("#cal-root")).to_be_visible()

    def test_calendar_view_shows_months(self, page: Page, server_url: str):
        """Calendar view displays month sections."""
        page.goto(f"{server_url}/?view=calendar")

        # Should have at least one month section
        expect(page.locator(".cal-month").first).to_be_visible()

    def test_calendar_view_has_day_headers(self, page: Page, server_url: str):
        """Calendar view has day-of-week headers."""
        page.goto(f"{server_url}/?view=calendar")

        expect(page.locator(".cal-header-cell").first).to_contain_text("Mon")


class TestActivityLinks:
    """Tests for activity card links and actions."""

    def test_activity_name_links_to_detail(self, page: Page, server_url: str):
        """Activity name links to detail page."""
        page.goto(server_url)

        # First activity link
        link = page.locator(".activity-name a").first
        expect(link).to_have_attribute("href", "/activity/12345")

    def test_enroll_button_links_externally(self, page: Page, server_url: str):
        """Enroll button links to external enrollment page."""
        page.goto(server_url)

        enroll_btn = page.locator(".btn-enroll").first
        expect(enroll_btn).to_have_attribute("href", "https://example.com/enroll/12345")
        expect(enroll_btn).to_have_attribute("target", "_blank")


class TestPagination:
    """Tests for pagination controls."""

    def test_pagination_info_shown(self, page: Page, server_url: str):
        """Pagination info shows current page."""
        page.goto(server_url)

        expect(page.locator(".pagination-info")).to_contain_text("Page 1 of 2")

    def test_next_button_visible(self, page: Page, server_url: str):
        """Next page button is visible when more pages exist."""
        page.goto(server_url)

        expect(page.locator(".pagination .btn")).to_contain_text("Next")
