# Mission — Common Pot

## Problem

When a group of people share expenses — on a trip, a shared flat, a team event, or any joint activity — tracking who paid for what and who owes whom becomes messy quickly. People use chat messages, spreadsheets, or memory, all of which are error-prone and hard to consult on the go.

## Solution

**Common Pot** — a lightweight, mobile-first web application that lets a group track shared expenses in real time and always shows a clear, up-to-date picture of who owes what to whom.

Any pot member can open the app in their phone browser, log a Drop, and the balances update instantly for everyone.

## Core Concepts

- **Pot** — a named collection of people sharing expenses for a common activity (e.g. "Italy Trip 2026", "Shared Flat 2026")
- **Member** — a participant in a pot, identified by their Telegram account
- **Drop** — an amount paid by one member, to be split among all or a defined subset of members
- **Split** — the share of a Drop assigned to each affected member
- **Balance** — the net position of each member (positive = owed money, negative = owes money)
- **Settlement** — a suggested set of transfers that brings all balances to zero

## Identity & Access

- Members authenticate via **Telegram Login** — no separate account needed
- The same Telegram user across multiple pots is the same person
- Each pot has an **invite link** — share it with someone, they authenticate with Telegram and join the pot
- The invite link is a convenience for sharing, not a security mechanism

## Interfaces

- **Web UI** — mobile-first browser interface, the primary interface
- **Telegram bot** (post-MVP) — members can add Drops directly from a Telegram group chat

## Goals

- Support multiple independent pots, each tracking their own expenses
- Make it effortless to log a Drop from a mobile phone in under 30 seconds
- Always show each member a clear view of what they owe and to whom
- Minimize the number of transfers needed to settle all debts
- Require no installation — just a URL shared within the pot
- Authenticate via Telegram — no separate registration needed

## Non-Goals (for MVP)

- Native mobile app
- Multi-currency support
- Recurring Drops
- Receipts or photo attachments
- Integration with payment systems (e.g. PayPal, Revolut)
- Email or push notifications
- Telegram bot interface (post-MVP)
