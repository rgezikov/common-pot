# Phase 19 — Definition of Done

- [x] Amount and weight fields accept `,` as a decimal separator (normalized to `.` before parsing)
- [x] Weight fields are blank by default — not pre-filled, and not a fake placeholder that looks filled but isn't
- [x] Add-drop form preserves typed weight values across a validation error (previously reset to blank/garbage)
- [x] "Split equally" sets every weight field to 1; "Clear all" blanks every field
- [x] Weight inputs have no up/down spinner arrows
- [x] Split help text is hidden behind an "ⓘ" button and centered on screen — doesn't overflow off-screen on narrow phones
- [x] Pot detail page no longer shows a drop-total next to the "Drops" heading
- [x] All existing and new behavior covered by tests (`pots/tests/test_integration.py`)
