# Phase 2 — Definition of Done

- [ ] Telegram Login Widget integrated — user can authenticate via Telegram in the browser
- [ ] Authenticated user's Telegram ID and name stored in the session
- [ ] Create a new pot (name, optional description) — only for authenticated users
- [ ] Invite link generated automatically on pot creation (`/join/<invite_token>/`)
- [ ] User can join a pot via invite link — authenticated via Telegram, added as a Member
- [ ] Joining the same pot twice is handled gracefully (no duplicate members)
- [ ] Home page shows all pots the logged-in user is a member of
- [ ] Pot detail page shows pot name, description, and member list
- [ ] Unauthenticated users are redirected to login
- [ ] Works correctly on a mobile browser
