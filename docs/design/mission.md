# Mission — Common Pot

## Problem

When a group of people share expenses — on a trip, a shared flat, a team event, or any joint activity — tracking who paid for what and who owes whom becomes messy quickly. People use chat messages, spreadsheets, or memory, all of which are error-prone and hard to consult on the go.

## Solution

**Common Pot** — a lightweight, mobile-first web application that lets a group track shared expenses in real time and always shows a clear, up-to-date picture of who owes what to whom.

Any pot member can open the app in their phone browser, log a payment, and the balances update instantly for everyone.

## Core Concepts

- **Pot** — a named collection of people sharing expenses for a common activity (e.g. "Italy Trip 2026", "Shared Flat 2026")
- **Member** — a participant in a pot
- **Drop** — an amount paid by one member, to be split among all or a defined subset of members
- **Split** — the share of a Drop assigned to each affected member
- **Balance** — the net position of each member (positive = owed money, negative = owes money)
- **Settlement** — a suggested set of transfers that brings all balances to zero

## Goals

- Support multiple independent pots, each tracking their own expenses
- Make it effortless to log an expense from a mobile phone in under 30 seconds
- Always show each member a clear view of what they owe and to whom
- Minimize the number of transfers needed to settle all debts
- Require no installation — just a URL shared within the pot
- Access control via secret link — no login required

## Non-Goals (for MVP)

- User accounts or cross-pot identity (same person in two pots is two separate members)
- Native mobile app
- Multi-currency support
- Recurring expenses
- Receipts or photo attachments
- Integration with payment systems (e.g. PayPal, Revolut)
- Email or push notifications
