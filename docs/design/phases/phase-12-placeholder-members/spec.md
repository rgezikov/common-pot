# Phase 12 — Placeholder Members

> Allow one member to create a pot and add others by name as placeholders, before those people have a Telegram account or have joined the app. Real members can claim a placeholder later and get full access.

## Problem

Currently all members must join via Telegram. This prevents the common case where one person wants to start tracking expenses for a group immediately, without waiting for everyone to register.

## Concept

A pot owner can add **placeholder members** — named slots not yet linked to a Telegram account. Expenses can be assigned to them just like real members. When the actual person registers via Telegram, the owner sends them a claim link. The person follows the link, logs in with Telegram, and is merged into the placeholder slot — all historical drops and balances carry over.

## Claim flow

1. Owner adds a placeholder member by name in pot settings.
2. Owner generates a claim link for that placeholder — the existing pot invite URL with an extra parameter (e.g. `join/<token>?claim=<placeholder_id>`).
3. Owner sends the link to the real person (e.g. via Telegram chat).
4. The real person opens the link, logs in with Telegram if not already, and confirms the claim.
5. The placeholder is replaced by the real member; all drops, splits, and balances transfer.

## Constraints

- Claim links expire after 1 hour.
- If the link expires, the owner generates a new one.
- A real member who already has a slot in the same pot cannot claim a placeholder — blocked.
- No revoke: expiry is sufficient. Sending to the wrong person is handled by waiting out the 1 hour.

## Constraints — bot commands

Placeholder members cannot be referenced in bot commands (`/paid`, `/split`). Use the web app to manage drops involving placeholders. Bot support for placeholder members is post-MVP.

## Drop timestamps

Each drop records two automatic timestamps:

- `created_at` — when the drop was first logged; used for chronological ordering in the drop list.
- `updated_at` — when the drop was last edited.

Display: show `created_at` always. If `updated_at` differs from `created_at`, append "edited on April 11, 23:15".

## Tasks

- Add `created_at` and `updated_at` timestamp fields to the Drop model
- Order drop list by `created_at`
- Display `created_at` date and time in drop listings
- Append "edited on ..." if `updated_at` differs from `created_at`
- Add a "placeholder" flag to the Member model
- Allow pot owner to add placeholder members by name (no Telegram account required)
- Generate a time-limited claim link per placeholder (1-hour expiry)
- Handle claim: verify link, verify claimer has no existing slot in the pot, merge placeholder into real member
- Transfer all drops, splits, and balances on claim
- Show placeholders in `/balance` and `/settle` output by name
