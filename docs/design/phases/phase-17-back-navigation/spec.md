# Phase 17 — Back-Button Navigation

> Make the browser back button behave as an "up" button throughout the app.

## Problem

Form submissions that redirect back to the same page pushed duplicate entries onto the browser history stack. As a result, pressing back stepped through previous states of the same page instead of going up to the parent screen. The "↑" up-navigation links also pushed new history entries, so pressing back after using one returned to the page you just left.

## Changes

**AJAX form submissions** — any form that posts and redirects back to the same page is intercepted with `fetch`. The DOM is updated in place; no history entry is created. Affects: add/toggle/delete item on list_detail, add/edit drop, create pot, create list, rename pot, rename list, add placeholder, ping bot.

**`history.replaceState` on view pages** — list_detail, pot_detail, and drop_detail each replace their own history entry on load, so repeated reloads of the same page don't stack.

**`pageshow` refresh** — when a view page is restored from the browser's back-forward cache, it re-fetches its dynamic content (items, drops, balances, pot/list name) so stale data is never shown after returning via back.

**`location.replace()` for "↑" links** — clicks on any link whose text starts with "↑" navigate via `location.replace()` instead of a normal link click. This replaces the current history entry rather than pushing a new one, so pressing back after going up does not return to the page you left.

**Edit pages** (`edit_item`, `edit_drop`) — the save form is submitted via `fetch`; on success the server redirects to the parent view and the browser calls `history.back()` to return there, keeping the edit page out of the forward history.
