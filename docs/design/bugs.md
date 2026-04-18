# Known Bugs

## B-1 — Member names are not unique identifiers

**Symptom**: Two members with the same first + last name in one pot are
indistinguishable in the UI and in bot commands (`/split Name:weight`,
`/paid Name`). Also affects the same real person joining from two Telegram
accounts — both get the same auto-generated display name.

**Root cause**: `Member.name` is built from `first_name + last_name` at join
time and is used as the display identifier everywhere. There is no uniqueness
constraint on `(pot, name)`.

**Impact**:
- UI shows duplicate names with no way to tell them apart
- Bot `/split` and `/paid` name lookups silently resolve to the wrong member
- Drops may be attributed to the wrong person

**Proposed fix**: Append a short disambiguator derived from `telegram_user_id`
to the display name when a collision exists, e.g. "Roman G #4712".
Alternatively, show Telegram username (if set) alongside the name.
