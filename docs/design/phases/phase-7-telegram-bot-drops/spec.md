# Phase 7 — Telegram Bot: Add Drops

> Allow members to log Drops directly from a Telegram group chat.

## Concepts

- Each Telegram group chat maps to exactly one Pot
- When the bot is added to a group, it creates a Pot for that chat (or links to an existing one)
- The bot provides the web invite link so members can join the Pot in the web UI
- Drop creation via bot shares the same business logic as the web UI

## Tasks

- Bot detects when it is added to a group chat and creates a linked Pot
- Bot responds to a command (e.g. `/start` or `/invite`) with the web invite link for the pot
- Members can log a Drop via the bot (description, amount, payer) — split equally among all pot members
- Bot confirms the Drop was recorded
