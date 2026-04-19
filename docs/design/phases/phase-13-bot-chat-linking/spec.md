# Phase 13 — Bot Chat Linking Improvements

> Make it easy to see and manage which Telegram chat is connected to a pot.

## Pot settings: bot status

The Pot Settings page shows the current bot connection state:

- Bot name (`@common_pot_bot`) if configured, or "Not configured — notifications disabled."
- If a chat is linked: the chat title, fetched live from the Telegram `getChat` API.
- If no chat is linked: an instruction showing the `/pot <invite_url>` command to use in Telegram.
- A **Send test message** button (when a chat is linked) that posts a test message to the chat so the user can verify the correct group is connected.

## Bot: /pot unlink

New `/pot unlink` subcommand detaches the current chat from its pot. Needed when a chat was accidentally linked to the wrong pot (e.g. via `/pot new`) and the user wants to link it to a different one.

## Bot: error handling

- `/pot <token>` now reports clearly if the chat is already linked to a different pot ("Use `/pot unlink` first").
- `/pot <token>` reports if the pot is already linked to this same chat.
- The entire `/pot` handler is wrapped in try/except so any unhandled exception produces a user-visible error reply instead of silent failure.
