# Phase 20 — Definition of Done

- [x] Drops can be marked as a settlement/repayment via a checkbox on the web add/edit forms
- [x] Drops can be marked as a settlement/repayment via a `/settlement` flag on the bot's `/drop` command
- [x] Settlement drops still count toward Paid, Owed, and Balance (balance math unaffected)
- [x] Settlement drops are excluded from the new "spent" / Spending total
- [x] Pot detail page shows a "Spending" section per member
- [x] Settlement drops are visibly badged in the drop list and on the drop detail page
- [x] Printable report shows a "True Expenses" section with a total, and marks settlement drops
- [x] Bot's `/help`, `/drop` usage/error messages, and the web Help page all document `/settlement` and the checkbox
- [x] Bot `/help` renders the `/drop` line's bracket notation correctly in Telegram (no more mangled `[...]`)
- [x] Migration applied to production with a pre-migration `db.sqlite3` backup taken first
- [x] Full test suite passes (`pots/tests/test_balances.py`, `test_integration.py`, `test_bot_parser.py`)
