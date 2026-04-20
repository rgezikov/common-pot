# Phase 16 — Site Owner Statistics

> Give maintainers a dashboard showing platform-wide usage metrics.

## Access control

An `is_maintainer` boolean field on `CompotUser` gates access. Set it to `True` via the Django admin on the user's CompotUser record. Non-maintainers get a 403.

## Features

- Total counts: users, pots, drops, lists, list items
- Activity over time: drops and list items added per day/week

## Notes

Implemented as a dedicated stats page (not inside Django admin). Non-maintainers get a 403.
