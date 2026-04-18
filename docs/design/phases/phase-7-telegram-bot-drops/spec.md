# Phase 7 — Telegram Bot: Add Drops

> Allow members to log Drops directly from a Telegram group chat.

## Concepts

- Each Telegram group chat maps to exactly one Pot
- When the bot is added to a group, it creates a Pot for that chat (or links to an existing one)
- The bot provides the web invite link so members can join the Pot in the web UI
- Drop creation via bot shares the same business logic as the web UI
- Bot runs as a separate systemd service (`commonpot-bot.service`)

## Command syntax

```
/drop <amount> <description> [@payer]
```

- `amount` — first token, numeric (formulas not supported via bot)
- `description` — everything after amount up to optional `@payer`; may be quoted with `'` or `"` (optional)
- `@payer` — optional; must be a pot member by Telegram username; defaults to message sender
- Split is always equal among all pot members (Phase 7)

### Examples

```
/drop 120 team dinner
/drop 120 "team dinner after work"
/drop 120 team dinner @Bob
/drop 45.50 'taxi home' @Alice
```

## Post-MVP extension (Phase 8+)

Weighted split after a comma:
```
/drop 120 team dinner @Bob, Alice:2 Carol:1
```

## Commands

- `/pot new` — create a new pot for this group chat (named after the chat)
- `/pot <invite_token>` — link this group chat to an existing pot from the web UI
- `/start` or `/invite` — reply with the web invite link for the linked pot
- `/drop <amount> <description> [@payer]` — log a drop; split equally among all pot members

## Tasks

- Bot added to a group: welcome message explaining `/pot new` and `/pot <token>`
- `/pot` command handles both `new` and token cases
- `/drop` without a linked pot replies with instructions to use `/pot` first
- Bot confirms drop was recorded with a summary
- Bot handles errors gracefully (no pot, unknown payer, invalid amount)
- Deployed as `commonpot-bot.service` systemd service
