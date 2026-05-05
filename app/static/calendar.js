/**
 * calendar.js — popup interaction for the calendar view.
 *
 * Each pill carries data-activity-id; the popup is populated by cloning the
 * matching hidden activity card from #cal-popup-sources. This keeps the popup
 * visually identical to a regular card without duplicating the markup.
 */

(function () {
    'use strict';

    var popup = document.getElementById('cal-popup');
    var backdrop = document.getElementById('cal-popup-backdrop');
    var closeBtn = document.getElementById('cal-popup-close');
    var content = document.getElementById('cal-popup-content');
    var sources = document.getElementById('cal-popup-sources');

    if (!popup || !backdrop || !closeBtn || !content || !sources) {
        return;
    }

    function getSourceCard(activityId) {
        return sources.querySelector(
            '.cal-popup-card-source[data-activity-id="' + activityId + '"]'
        );
    }

    function renderPopup(activityId) {
        var source = getSourceCard(activityId);
        if (!source) {
            content.innerHTML = '';
            return false;
        }
        content.innerHTML = '';
        var card = source.firstElementChild;
        if (!card) return false;
        content.appendChild(card.cloneNode(true));
        return true;
    }

    // ── Positioning ───────────────────────────────────────────────────────────

    function positionPopup(triggerEl) {
        popup.style.left = '';
        popup.style.top = '';
        popup.style.right = '';
        popup.style.bottom = '';

        var rect = triggerEl.getBoundingClientRect();
        var popupWidth = popup.offsetWidth || 300;
        var margin = 8;
        var viewportWidth = window.innerWidth;
        var viewportHeight = window.innerHeight;

        var left = rect.right + margin;
        if (left + popupWidth > viewportWidth - margin) {
            left = rect.left - popupWidth - margin;
        }
        left = Math.max(margin, left);

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
    var activeActivityId = null;

    function openPopup(triggerEl, activityId) {
        if (!renderPopup(activityId)) return;
        activeTrigger = triggerEl;
        activeActivityId = activityId;
        popup.hidden = false;
        backdrop.hidden = false;
        positionPopup(triggerEl);
        closeBtn.focus();
    }

    function closePopup() {
        popup.hidden = true;
        backdrop.hidden = true;
        activeActivityId = null;
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

            if (activeTrigger === pill && !popup.hidden) {
                closePopup();
                return;
            }

            var activityId = pill.getAttribute('data-activity-id');
            if (!activityId) return;
            openPopup(pill, activityId);
        });
    }

    closeBtn.addEventListener('click', closePopup);
    backdrop.addEventListener('click', closePopup);

    document.addEventListener('keydown', function (e) {
        if ((e.key === 'Escape' || e.key === 'Esc') && !popup.hidden) {
            closePopup();
        }
    });

    // ── Wishlist toggle inside popup ──────────────────────────────────────────
    // Sync the source card and pills so reopening reflects the new state.

    content.addEventListener('click', function (e) {
        var btn = e.target.closest('.wishlist-btn');
        if (!btn) return;
        e.preventDefault();
        toggleWishlist(btn, syncWishlistState);
    });

    function syncWishlistState(activityId, newWishListId) {
        var isOn = newWishListId > 0;

        // Sync the hidden source card's heart so the next open is correct.
        var source = getSourceCard(activityId);
        if (source) {
            var srcBtn = source.querySelector('.wishlist-btn');
            if (srcBtn) {
                srcBtn.setAttribute('data-wish-list-id', String(newWishListId));
                srcBtn.classList.toggle('wishlisted', isOn);
                srcBtn.textContent = isOn ? '♥' : '♡';
            }
        }

        // Update any pills for this activity to show/hide the heart prefix.
        var pills = document.querySelectorAll(
            '.cal-event-pill[data-activity-id="' + activityId + '"]'
        );
        for (var i = 0; i < pills.length; i++) {
            var nameSpan = pills[i].querySelector('.cal-event-name');
            if (!nameSpan) continue;
            var text = nameSpan.textContent.replace(/^♥\s*/, '');
            nameSpan.textContent = (isOn ? '♥ ' : '') + text;
        }
    }

    // Reposition on resize (popup is position:fixed, so no scroll handler needed).
    var repositionTimer = null;
    window.addEventListener('resize', function () {
        if (repositionTimer) clearTimeout(repositionTimer);
        repositionTimer = setTimeout(function () {
            if (!popup.hidden && activeTrigger) {
                positionPopup(activeTrigger);
            }
        }, 100);
    });

}());
