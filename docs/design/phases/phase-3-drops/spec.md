# Phase 3 — Drops

> Allow members to log Drops.

## Tasks

- Set up pytest and pytest-django for testing
- Add a Drop: description, amount, payer, date
- Split Drop equally among all pot members (default)
- Split Drop among a selected subset of members
- List all Drops in a pot (most recent first)
- View Drop detail (who paid, how it was split)

## Testing

- Set up GitHub Actions workflow to run pytest on every push
- Unit tests for split calculation logic (equal split, subset split)
- All business logic must have passing tests before this phase is done
