# UI Guidelines

## Color Scheme

The app must be usable in a wide range of lighting conditions — from bright sunlight on a beach or boat deck to a dark cabin or bedroom at night. 

- **Dark mode by default** — the app launches in dark mode
- Provide a manual toggle to switch to light mode (Phase 6)
- Implemented via Tailwind's `class` dark mode strategy (`class="dark"` on `<html>`)
- Colors must have sufficient contrast in both modes (WCAG AA minimum)

## Mobile-First

- Touch-friendly tap targets (minimum 44px height)
- Single-column layouts
- Minimal typing — prefer dropdowns and pickers over free text where possible

## Performance

- HTMX partial updates — avoid full page reloads
- No heavy JavaScript frameworks
- Fast initial load on a mobile connection
