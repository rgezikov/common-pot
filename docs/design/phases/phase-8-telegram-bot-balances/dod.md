# Phase 8 — Definition of Done

## Commands

- `/balances` — posts per-member balance table (Paid / Owed / Net) sorted by net balance descending
- `/settle` — posts minimal settlement transfers; replies "All settled up!" when no transfers needed
- Both commands work only in group chats linked to a pot; reply with guidance otherwise

## Notifications

- Adding a drop via the web UI posts a notification to the linked group chat (if any)
- Notification includes description, amount, payer name, and a link to open the pot
- Drops added via bot do not trigger a duplicate notification

## UX

- `/link` command sends two links: **Open pot** (public, no auth) and **Join pot** (auth required)
  — solves the mobile WebView issue where the internal browser has no session
- Bot messages use Markdown with human-readable link labels instead of raw URLs

## Tested

- `/balances` and `/settle` verified in a live group chat
- Web UI drop notification received in linked group
- `/link` two-link response verified; Open pot link works in Telegram WebView without login
