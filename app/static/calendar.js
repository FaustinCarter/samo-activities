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
    // eventData shape is defined by CalendarEvent.popup_dict() in
    // app/models/calendar.py and serialized into each pill's data-event attr.

    function renderPopup(eventData) {
        var dateRange = formatDateRange(eventData.date_range_start, eventData.date_range_end);
        var timeStr = '';
        if (eventData.starting_time) {
            timeStr = eventData.starting_time;
            if (eventData.ending_time) {
                timeStr += ' \u2013 ' + eventData.ending_time;
            }
        }

        var spotsStr = '';
        if (eventData.total_open !== null && eventData.total_open !== undefined) {
            if (eventData.already_enrolled !== null && eventData.already_enrolled !== undefined) {
                var remaining = eventData.total_open - eventData.already_enrolled;
                spotsStr = remaining + ' of ' + eventData.total_open + ' spots open';
            } else {
                spotsStr = eventData.total_open + ' spots open';
            }
        }

        var rows = '';
        if (eventData.number) rows += metaRow('Number', eventData.number);
        if (dateRange)        rows += metaRow('Dates',  dateRange);
        if (timeStr)          rows += metaRow('Time',   timeStr);
        if (eventData.location) rows += metaRow('Location', eventData.location);
        if (eventData.ages)   rows += metaRow('Ages',   eventData.ages);
        if (spotsStr)         rows += metaRow('Spots',  spotsStr);

        var actionsHtml =
            '<a href="/activity/' + escapeHtml(String(eventData.id)) + '" class="btn">' +
            'View details</a>';

        // Wishlist toggle button (only when wish_list_id is present in data)
        if (eventData.wish_list_id !== undefined) {
            var isWishlisted = eventData.wish_list_id > 0;
            actionsHtml +=
                '<button class="btn wishlist-btn' +
                (isWishlisted ? ' wishlisted' : '') + '"' +
                ' data-activity-id="' + escapeHtml(String(eventData.id)) + '"' +
                ' data-wish-list-id="' + escapeHtml(String(eventData.wish_list_id)) + '">' +
                (isWishlisted ? '\u2665 Wishlisted' : '\u2661 Wishlist') +
                '</button>';
        }

        if (eventData.action_link_href) {
            var enrollClass = eventData.action_link_type === 3 ? 'btn-enroll' : 'btn-waitlist';
            actionsHtml +=
                '<a href="' + escapeHtml(eventData.action_link_href) + '" ' +
                'class="btn ' + enrollClass + '" target="_blank" rel="noopener">' +
                escapeHtml(eventData.action_link_label || 'Enroll') + '</a>';
        } else if (eventData.notification) {
            actionsHtml +=
                '<span class="cal-popup-closed">' +
                escapeHtml(eventData.notification) + '</span>';
        }

        content.innerHTML =
            '<p class="cal-popup-title">' + escapeHtml(eventData.name) + '</p>' +
            '<div class="cal-popup-color-bar" style="background:' + escapeHtml(eventData.color) + '"></div>' +
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

    // ── Wishlist toggle in popup (delegates to shared toggleWishlist) ─────────

    content.addEventListener('click', function (e) {
        var btn = e.target.closest('.wishlist-btn');
        if (!btn) return;
        toggleWishlist(btn, updatePillWishlistState);
    });

    function updatePillWishlistState(activityId, newWishListId) {
        // Update all pills for this activity across the calendar
        var pills = document.querySelectorAll('.cal-event-pill');
        for (var i = 0; i < pills.length; i++) {
            var raw = pills[i].getAttribute('data-event');
            if (!raw) continue;
            try {
                var ev = JSON.parse(raw);
                if (String(ev.id) !== String(activityId)) continue;
                ev.wish_list_id = newWishListId;
                pills[i].setAttribute('data-event', JSON.stringify(ev));
                var nameSpan = pills[i].querySelector('.cal-event-name');
                if (nameSpan) {
                    var baseName = ev.name;
                    nameSpan.innerHTML = (newWishListId > 0 ? '&hearts; ' : '') + escapeHtml(baseName);
                }
            } catch (err) {
                // skip
            }
        }
    }

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
