# Phase 18.1 — Shopping List Menu

> Replace the gear icon with a hamburger menu that groups list actions.

## Problem

The gear icon linked directly to settings. There was no way to act on multiple items at once — deleting checked items required tapping ✕ on each one individually.

## Changes

**Hamburger menu (☰)** — replaces the ⚙ gear link in the list header. Clicking opens a dropdown; clicking anywhere outside closes it. Same pattern as the home screen ⋮ menu.

**Settings** — first menu item, navigates to the existing list settings screen.

**Delete selected** — second menu item. Shows a confirmation dialog, then POSTs to the new `delete_checked_items` endpoint via AJAX and refreshes the item list in place. No page navigation occurs.

**`delete_checked_items` view** — new endpoint at `POST /list/<token>/items/delete-checked/`. Deletes all `Item` rows with `checked=True` for the given list. Auth guard identical to other list views (must be a list member). Redirects back to `list_detail`, which the AJAX handler parses to update the DOM.
