# Phase 2 — Definition of Done

- [x] Telegram Login integrated — user can authenticate via Telegram in the browser (same-window redirect)
- [x] Authenticated user's Telegram ID and name stored in the session
- [x] Create a new pot (name, optional description) — only for authenticated users
- [x] Invite link generated automatically on pot creation (`/join/<invite_token>/`)
- [x] User can join a pot via invite link — authenticated via Telegram, added as a Member
- [x] Joining the same pot twice is handled gracefully (no duplicate members)
- [x] Home page shows all pots the logged-in user is a member of
- [x] Pot detail page shows pot name, description, and member list
- [x] Unauthenticated users are redirected to login (with `next` URL preserved)
- [x] Works correctly on a mobile browser
