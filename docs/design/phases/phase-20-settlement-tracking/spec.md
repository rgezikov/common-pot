# Phase 20 — Settlement / Repayment Tracking

> Distinguish "real shared expense" from "money moved to settle up" so member spending totals reflect actual costs.

## Problem

Members sometimes record a repayment as a Drop — e.g. B pays A back 50, logged as a drop paid by B, split 100% to A, to zero out an existing balance. This is a legitimate way to settle up, but the app had no way to tell that drop apart from a real shared expense: it was included in the "Owed" total the same as any other split, inflating the recipient's apparent spending by the repayment amount.

Concretely: A pays 100 for something shared 50/50 with B (A: owed 50, B: owed 50). B then pays A back 50 (a repayment, split 100% to A). Before this phase, A's "Owed" total read 100 (50 real + 50 from the repayment) even though A only actually spent 50.

## Changes

- **`Drop.is_settlement`** — new boolean field (migration `0010_drop_is_settlement`), default `False`.
- **Web forms** (`add_drop.html`, `edit_drop.html`) — "This is a settlement / repayment (excluded from spending totals)" checkbox.
- **`calculate_balances`** — now also returns `spent` per member: identical accumulation to `owed`, but skips drops where `is_settlement` is true. `paid`/`owed`/`balance` are unchanged, since settlement drops must still count there for the balance math to correctly zero out.
- **Pot detail page** — new "Spending" section (member → spent total, excludes settlements); settlement drops get a small "Settlement" badge in the drop list and on the drop detail page.
- **Printable report** (`pot_report.html`) — new "True Expenses" section (member × spent, with a total); settlement drops marked "(settlement)" next to their description in the drops table.
- **Telegram bot** — `/drop` gained a standalone `/settlement` flag token, parsed by `resolve_member_specs` (now returns `is_settlement` as a 4th value) and persisted via `_create_drop_sync`. Distinct from the pre-existing `/settle` command, which only *shows* suggested transfers and doesn't record anything. The bot's confirmation message notes when a drop was marked as a settlement.
- **Docs** — the web Help page and every bot usage/error string were updated to document the checkbox and the `/settlement` flag, with `/drop`'s optional parameters shown in `[brackets]` (including `[:weight]` being optional within `/split`).
- **Bug fix found along the way**: the bot's `/help` message uses `parse_mode='Markdown'`, and Telegram's legacy Markdown parser treats an unescaped `[` as the start of link syntax — the bracket notation in the `/drop` help line was being silently mangled in the actual Telegram UI. Fixed by escaping every literal bracket (`\[` `\]`), the same convention already used for `<invite\_token>`.

## Operational note

This phase shipped a schema migration to production. Process used: back up `db.sqlite3` on the server (`cp db.sqlite3 db.sqlite3.bak-<timestamp>`) before running `migrate`, since the migration is additive and trivially reversible (`migrate pots 0009_compotuser_is_maintainer` drops the column again) but a raw file backup is a free extra safety net for a single-file SQLite deployment.

## Out of scope / known limitation

Existing drops (including ones already used as an informal repayment convention, e.g. before this phase) are **not** retroactively marked — `is_settlement` defaults to `False`. Any old repayment drop needs to be edited and the checkbox ticked for it to be excluded from Spending.
