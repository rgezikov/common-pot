# Phase 9 — Definition of Done

- Telegram WebApp `initData` verified server-side with HMAC-SHA256 (`WebAppData` key derivation)
- `POST /auth/webapp/` endpoint authenticates the user and returns `next` URL for redirect
- `base.html` loads the Telegram WebApp SDK and auto-authenticates on page load when `initData` is present
- Both links from `/link` work inside Telegram WebView without a login screen:
  - **Open pot** — already public, unchanged
  - **Join pot** — now authenticates silently via WebApp initData, then joins and shows the pot
- OAuth login remains available as fallback for desktop and direct browser access
