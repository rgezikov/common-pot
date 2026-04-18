# Phase 9 — Telegram Mini App

> Open the pot directly from Telegram without a login screen.

## Problem

On mobile, Telegram opens links in its internal WebView which has no session
and no access to the system browser's cookies. Clicking a pot link shows the
login screen, and "Login with Telegram" falls back to phone number entry
because `oauth.telegram.org` can't recognise the user in the WebView.

On desktop this works fine because the system browser has the Telegram web
session. On mobile it is a poor experience.

## Solution

Convert to a Telegram Mini App (WebApp). When a Mini App is opened, Telegram
injects the user's identity directly via `window.Telegram.WebApp.initDataUnsafe.user`
— no OAuth flow, no login screen. The server verifies the `initData` HMAC
signature instead of the OAuth hash.

This also enables a natural entry point: a button on the bot that opens the
pot directly inside Telegram.

## Tasks

- Add a Mini App entry point to the bot (`/open` command or inline button)
- Verify Telegram WebApp `initData` on the server (HMAC-SHA256, same key as OAuth)
- Replace OAuth login with WebApp auth when running inside Telegram Mini App
  (keep OAuth as fallback for desktop/direct browser access)
- Bot sends an inline keyboard button "Open pot" that launches the Mini App
