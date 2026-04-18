# Phase 8 — Telegram Bot: Balances & Settlements

> Allow members to check the pot's financial state from Telegram.

## Commands

- `/balances` — show current balances for all members (Paid, Owed, Net)
- `/settle` — show settlement suggestions ("Alice pays Bob X")

## Notifications

- When a drop is added via the **web UI**, the bot posts a notification to the linked group chat
- Drops added via bot are already visible in the chat — no notification needed

## Tasks

- `/balances` command: show per-member balance summary
- `/settle` command: show minimal settlement transfers
- Web UI drop creation triggers a Telegram notification to the linked group (if any)
