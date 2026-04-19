# Phase 13 — Definition of Done

- [x] Pot Settings page shows bot name when configured, or "Not configured" when not
- [x] Pot Settings page shows linked Telegram chat title (fetched live) when a chat is linked
- [x] Pot Settings page shows `/pot <invite_url>` instruction when no chat is linked
- [x] "Send test message" button visible when chat is linked; pressing it posts a message to the group and shows a confirmation flash
- [x] `/pot unlink` command detaches the chat from its pot and confirms in the group
- [x] `/pot <token>` reports an error when the chat is already linked to a different pot
- [x] `/pot <token>` reports an error when the pot is already linked to this same chat
- [x] All `/pot` errors are reported as bot replies (no silent failures)
