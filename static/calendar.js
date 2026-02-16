/**
 * calendar.js — popup interaction for the calendar view.
 *
 * Attaches click handlers to every .cal-event-pill button. When clicked the
 * popup (#cal-popup) is positioned near the pill and populated with the
 * activity details encoded in the button's data-event attribute.
 */

(function () {
    'use strict';

    var popup = document.getElementById('cal-popup');
    var backdrop = document.getElementById('cal-popup-backdrop');
    var closeBtn = document.getElementById('cal-popup-close');
    var content = document.getElementById('cal-popup-content');

    if (!popup || !backdrop || !closeBtn || !content) {
        // Not on a page that has the popup markup.
        return;
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    function formatDateRange(start, end) {
        if (!start) return '';
        if (!end || start === end) return formatDate(start);
        return formatDate(start) + ' \u2013 ' + formatDate(end);
    }

    function formatDate(isoStr) {
        if (!isoStr) return '';
        // Parse as local date to avoid timezone offset issues.
        var parts = isoStr.split('-');
        if (parts.length < 3) return isoStr;
        var d = new Date(
            parseInt(parts[0], 10),
            parseInt(parts[1], 10) - 1,
            parseInt(parts[2], 10)
        );
        return d.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function metaRow(label, value) {
        if (!value && value !== 0) return '';
        return (
            '<div class="cal-popup-meta-row">' +
            '<span class="cal-popup-meta-label">' + escapeHtml(label) + '</span>' +
            '<span>' + escapeHtml(String(value)) + '</span>' +
            '</div>'
        );
    }

    // ── Render popup content ──────────────────────────────────────────────────

    function renderPopup(event) {
        var dateRange = formatDateRange(event.date_range_start, event.date_range_end);
        var timeStr = '';
        if (event.starting_time) {
            timeStr = event.starting_time;
            if (event.ending_time) {
                timeStr += ' \u2013 ' + event.ending_time;
            }
        }

        var spotsStr = '';
        if (event.total_open !== null && event.total_open !== undefined) {
            spotsStr = event.total_open + ' open';
        }

        var rows = '';
        if (event.number) rows += metaRow('Number', event.number);
        if (dateRange)    rows += metaRow('Dates',  dateRange);
        if (timeStr)      rows += metaRow('Time',   timeStr);
        if (event.location) rows += metaRow('Location', event.location);
        if (event.ages)   rows += metaRow('Ages',   event.ages);
        if (spotsStr)     rows += metaRow('Spots',  spotsStr);

        var actionsHtml = '';
        actionsHtml +=
            '<a href="/activity/' + escapeHtml(String(event.id)) + '" class="btn">' +
            'View details</a>';
        if (event.action_link_href) {
            actionsHtml +=
                '<a href="' + escapeHtml(event.action_link_href) + '" ' +
                'class="btn btn-enroll" target="_blank" rel="noopener">' +
                escapeHtml(event.action_link_label || 'Enroll') + '</a>';
        }

        content.innerHTML =
            '<div class="cal-popup-color-bar" style="background:' + escapeHtml(event.color) + '"></div>' +
            '<p class="cal-popup-title">' + escapeHtml(event.name) + '</p>' +
            '<div class="cal-popup-meta">' + rows + '</div>' +
            '<div class="cal-popup-actions">' + actionsHtml + '</div>';
    }

    // ── Positioning ───────────────────────────────────────────────────────────

    function positionPopup(triggerEl) {
        popup.style.left = '';
        popup.style.top = '';
        popup.style.right = '';
        popup.style.bottom = '';

        var rect = triggerEl.getBoundingClientRect();
        var popupWidth = 280;
        var margin = 8;
        var viewportWidth = window.innerWidth;
        var viewportHeight = window.innerHeight;

        // Prefer opening to the right; fall back to left.
        // getBoundingClientRect() returns viewport-relative coords, and the
        // popup is position:fixed, so no scroll offset adjustment is needed.
        var left = rect.right + margin;
        if (left + popupWidth > viewportWidth - margin) {
            left = rect.left - popupWidth - margin;
        }
        // Clamp to viewport
        left = Math.max(margin, left);

        // Prefer opening below the trigger top; fall back to above.
        var top = rect.top;
        var popupHeight = popup.offsetHeight || 260;
        if (top + popupHeight > viewportHeight - margin) {
            top = rect.bottom - popupHeight;
        }
        top = Math.max(margin, top);

        popup.style.left = left + 'px';
        popup.style.top  = top  + 'px';
    }

    // ── Open / close ──────────────────────────────────────────────────────────

    var activeTrigger = null;

    function openPopup(triggerEl, eventData) {
        activeTrigger = triggerEl;
        renderPopup(eventData);
        popup.hidden = false;
        backdrop.hidden = false;
        positionPopup(triggerEl);
        closeBtn.focus();
    }

    function closePopup() {
        popup.hidden = true;
        backdrop.hidden = true;
        if (activeTrigger) {
            activeTrigger.focus();
            activeTrigger = null;
        }
    }

    // ── Event delegation on the calendar root ─────────────────────────────────

    var calRoot = document.getElementById('cal-root');
    if (calRoot) {
        calRoot.addEventListener('click', function (e) {
            var pill = e.target.closest('.cal-event-pill');
            if (!pill) return;
            e.stopPropagation();

            // If the same pill is clicked again, close.
            if (activeTrigger === pill && !popup.hidden) {
                closePopup();
                return;
            }

            var raw = pill.getAttribute('data-event');
            if (!raw) return;
            var eventData;
            try {
                eventData = JSON.parse(raw);
            } catch (err) {
                return;
            }
            openPopup(pill, eventData);
        });
    }

    closeBtn.addEventListener('click', closePopup);
    backdrop.addEventListener('click', closePopup);

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if ((e.key === 'Escape' || e.key === 'Esc') && !popup.hidden) {
            closePopup();
        }
    });

    // Reposition on scroll/resize (debounced)
    var repositionTimer = null;
    function handleResize() {
        if (repositionTimer) clearTimeout(repositionTimer);
        repositionTimer = setTimeout(function () {
            if (!popup.hidden && activeTrigger) {
                positionPopup(activeTrigger);
            }
        }, 100);
    }
    window.addEventListener('resize', handleResize);
    // No scroll handler needed: position:fixed popup stays with the viewport.

}());
