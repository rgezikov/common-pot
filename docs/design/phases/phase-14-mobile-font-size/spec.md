# Phase 14 — Mobile Font Size

> Increase the base font size on mobile browsers for better readability.

## Change

Add a CSS media query in `base.html` that sets `html { font-size: 18px; }` on screens ≤640px wide. The browser default is 16px, so this is a ~12.5% increase. Because Tailwind uses `rem` units, all text scales proportionally — no per-component changes needed.
