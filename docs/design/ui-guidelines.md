# UI Guidelines

## Color Scheme

The app must be usable in a wide range of lighting conditions — from bright sunlight on a beach or boat deck to a dark cabin or bedroom at night. 

- Support both **light mode** and **dark mode**
- Follow the device's system preference by default (`prefers-color-scheme`)
- Provide a manual toggle to override the system preference
- Colors must have sufficient contrast in both modes (WCAG AA minimum)

## Mobile-First

- Touch-friendly tap targets (minimum 44px height)
- Single-column layouts
- Minimal typing — prefer dropdowns and pickers over free text where possible

## Performance

- HTMX partial updates — avoid full page reloads
- No heavy JavaScript frameworks
- Fast initial load on a mobile connection
