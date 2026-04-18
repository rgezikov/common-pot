# Phase 7 — Definition of Done

- [x] Bot added to a group chat shows welcome message with instructions
- [x] `/pot new` creates a new pot linked to the group chat
- [x] `/pot <token>` links an existing pot — accepts both UUID and full invite URL
- [x] One pot per group chat; one group per pot (enforced)
- [x] `/link` replies with the web invite link for the linked pot
- [x] `/drop <amount> <description>` logs a drop, paid by sender, split equally among all members
- [x] `/drop <amount> <description> @payer` logs a drop paid by the specified member
- [x] Description may be quoted with single or double quotes
- [x] Bot replies with confirmation summary after each drop
- [x] Errors handled gracefully: no pot linked, unknown payer, invalid amount, bot specified as payer
- [x] All DB calls use sync_to_async (Django ORM compatible with async bot)
- [x] Bot runs as `commonpot-bot.service` systemd service
- [x] Copy-to-clipboard button for invite link in web Settings page
- [x] 12 unit tests for bot command parser
