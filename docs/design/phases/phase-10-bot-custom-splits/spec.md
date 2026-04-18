# Phase 10 — Telegram Bot: Custom Split Weights

> Allow members to specify per-member split weights directly in the `/drop` command.

## Command syntax

```
/drop <amount> [description] [/paid @username] [/split @username:weight, @username:weight ...]
```

- `/paid @username` — payer by Telegram username
- `/split @username:weight, ...` — custom split; members not listed are excluded
- Members must have a Telegram username to be referenced
- The Telegram name picker (which inserts `@username ` with a trailing space) is supported
- `/paid` and `/split` are recognised even without a leading space (e.g. `42/paid`)

## Examples

```
/drop 120 dinner
/drop 120 dinner /paid @alice
/drop 43 payback /paid @roman /split @roman:5, @rgezikov:8
```

## Tasks

- Add `/paid` and `/split` section parsing to bot_parser
- Comma-separated split items support names with spaces and `@username :weight` format
- Lookup by Telegram username only — no ambiguous name matching
- Sync `telegram_username` on every web app join and drop submission
- Fix split rounding: use ROUND_HALF_UP instead of ROUND_DOWN
