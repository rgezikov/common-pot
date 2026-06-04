# Phase 1003.1 — Shopping List: Manage Suggestions

> Allow users to edit and delete items in the suggestion list for a shopping list.

## Problem

Suggestions accumulate over time and can't be cleaned up. A typo or outdated item stays in the suggestion list forever, cluttering the autocomplete.

## Change

Add a "Manage suggestions" screen accessible from the shopping list view (e.g. via the list's hamburger menu). The screen shows all suggestions for that list and lets the user:

- **Delete** a suggestion — removes it permanently from the list's suggestion pool.
- **Edit** a suggestion — rename it in place (the stored name is updated; does not affect existing items).

### UI

- List all suggestions alphabetically.
- Each row has an edit (pencil) icon and a delete (trash) icon.
- Edit opens an inline field or small modal to rename the suggestion.
- Bulk delete is out of scope for this phase.

### Access

- Only list members can manage suggestions for a list.
- Accessible from the shopping list's hamburger menu: "Manage suggestions".

### Backend

- Edit: `POST /list/<id>/suggestion/<suggestion_id>/edit/` — updates `ListItemSuggestion.name`.
- Delete: `POST /list/<id>/suggestion/<suggestion_id>/delete/` — deletes the `ListItemSuggestion` row.
- Both views require list membership.
