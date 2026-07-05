# Phase 12.1 — Edit Placeholder Member Name

> Allow renaming a placeholder member after it has been added.

## Problem

Placeholder members ([[phase-12]]) could be added by name and given a claim
link, but there was no way to fix a typo or change the name afterwards — the
only options were to keep the wrong name or delete and re-add.

## Change

In the pot settings view, each placeholder in the "Placeholder Members" list
gets an edit (✏) action that reveals an inline rename field. Saving updates the
placeholder's name.

- Only applies to placeholder members (real members are not renamed here).
- Editing the name does not affect drops, splits, or balances — it only changes
  the displayed name of the `CompotUser` behind the placeholder slot.
- Uses the same in-place AJAX refresh as the rest of the settings section.

## Backend

- `POST /pot/<token>/placeholder/<member_id>/rename/` — updates
  `CompotUser.name` for the placeholder. Requires the member to belong to the
  pot and be a placeholder.
