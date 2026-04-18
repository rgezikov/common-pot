# Phase 10 — Definition of Done

- `/drop` command supports `/paid @username` and `/split @user:weight, ...` sections
- Section markers recognised without a leading space (e.g. `42/paid @alice`)
- Telegram picker format `@username :weight` (space before colon) handled correctly
- Members referenced by Telegram username only — no ambiguous name-based lookup
- `telegram_username` updated on every web app join and drop submission
- Split rounding uses ROUND_HALF_UP; last member gets exact remainder
- 48 tests passing
