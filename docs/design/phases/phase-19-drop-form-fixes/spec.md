# Phase 19 — Drop Form Usability Fixes

> Fix a cluster of small but real usability problems in the add/edit Drop forms, found from real usage.

## Problems

- **iPhone comma-decimal keyboards broke validation.** `inputmode="decimal"` shows a comma-only keypad on iPhones in comma-decimal locales. Python's `Decimal` rejects a comma separator, so `Amount` (and custom split `weight_*` fields) always failed validation with "Invalid amount".
- **Weight fields looked pre-filled but weren't.** The weight inputs used `placeholder="1"` (grey hint text). A user who left it untouched while zeroing every other member's field ended up submitting *all* weights as 0 — which silently falls back to an even split among everyone, instead of directing the drop to the one member they meant to leave alone.
- **Spinner arrows** cluttered the weight inputs (`type="number"`).
- **The pot detail page showed a drop-total** ("turnover") next to the "Drops" heading that added no useful information.

## Changes

- `_parse_drop_form` normalizes `,` → `.` for both the amount and every `weight_*` field before parsing.
- Weight fields default to genuinely blank (a real, submitted empty value) instead of a placeholder. Add/edit drop views build a `member_weights` list so blank/typed values round-trip correctly, including across a validation error re-render (add_drop previously lost this on error).
- Added **"Split equally"** and **"Clear all"** buttons above the weight list — one click sets every field to `1` or blanks them all, covering the two common cases (even split; split among a few people).
- Weight inputs switched from `type="number"` to `type="text" inputmode="decimal"` (matching the Amount field) — removes the spinner UI while keeping the mobile decimal keypad.
- The static split help paragraph was replaced with a tap-to-open "ⓘ" info button. The bubble is centered on screen with a dimmed backdrop (anchoring it to the button itself overflowed off-screen on narrow phones, since the button's horizontal position varies) and now also explains that weights are summed and shares are proportional to weight.
- Split label copy: "leave 0 to exclude" → "zero or empty to exclude" (blank is now the real default, not 0).
- Removed the drop-total figure shown above the drop list on the pot detail page. The printable report (`pot_report.html`) keeps its own total — this only affected the on-page summary.

## Out of scope

The Telegram bot's `/drop` command parses amounts with a plain `Decimal(amount_str)` too, so it doesn't accept a comma. Left as-is — the bot is a different input surface (typed chat text), not the reported problem.
