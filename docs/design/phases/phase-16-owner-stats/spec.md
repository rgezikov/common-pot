# Phase 16 — Site Owner Statistics

> Give maintainers a dashboard showing platform-wide usage metrics.

## Access control

A Django group named **Maintainers** gates access to the stats page. Users are added to the group via the Django admin. Any user in the Maintainers group can view the stats — no superuser required.

## Features

- Total counts: users, pots, drops, lists, list items
- Activity over time: drops and list items added per day/week

## Notes

Implemented as a dedicated stats page (not inside Django admin). Non-maintainers get a 403.
