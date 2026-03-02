/**
 * wishlist.js — Shared wishlist toggle logic.
 *
 * Provides toggleWishlist() used by:
 *   - Activity cards (index page, event delegation on .activity-grid)
 *   - Activity detail page (#detail-wishlist-btn)
 *   - Calendar popups (event delegation in calendar.js)
 *
 * All wishlist buttons use the .wishlist-btn class and the
 * ♡/♥ text style.  Each button must have data-activity-id and
 * data-wish-list-id attributes.
 */

/* exported toggleWishlist */

function toggleWishlist(btn, afterToggle) {
    var activityId = btn.getAttribute('data-activity-id');
    var wishListId = parseInt(btn.getAttribute('data-wish-list-id'), 10) || 0;

    if (wishListId > 0) {
        fetch('/api/wishlist/' + wishListId, { method: 'DELETE' })
            .then(function (res) {
                if (!res.ok) throw new Error(res.status);
                return res.json();
            })
            .then(function () {
                btn.setAttribute('data-wish-list-id', '0');
                btn.classList.remove('wishlisted');
                btn.textContent = '\u2661 Wishlist';
                if (afterToggle) afterToggle(activityId, 0);
            })
            .catch(function () {});
    } else {
        fetch('/api/wishlist/' + activityId, { method: 'POST' })
            .then(function (res) {
                if (!res.ok) throw new Error(res.status);
                return res.json();
            })
            .then(function (data) {
                var newId = data.wish_list_id || 0;
                btn.setAttribute('data-wish-list-id', String(newId));
                btn.classList.add('wishlisted');
                btn.textContent = '\u2665 Wishlisted';
                if (afterToggle) afterToggle(activityId, newId);
            })
            .catch(function () {});
    }
}

// Activity cards — event delegation on .activity-grid
(function () {
    var grid = document.querySelector('.activity-grid');
    if (!grid) return;

    grid.addEventListener('click', function (e) {
        var btn = e.target.closest('.wishlist-btn');
        if (!btn) return;
        e.preventDefault();
        toggleWishlist(btn);
    });
})();

// Detail page — single button
(function () {
    var btn = document.getElementById('detail-wishlist-btn');
    if (!btn) return;

    btn.addEventListener('click', function (e) {
        e.preventDefault();
        toggleWishlist(btn);
    });
})();
