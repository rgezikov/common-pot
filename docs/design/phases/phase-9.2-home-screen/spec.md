# Phase 9.2 — Add Pot to Home Screen

> Let users pin a pot directly to their phone's home screen.

## Tasks

- Serve a dynamic web app manifest per pot (`/pot/<token>/manifest.json`)
  with the pot's name as app name and `start_url` pointing to the pot
- Register a minimal service worker (`/sw.js`) to satisfy browser install requirements
- Add `<link rel="manifest">` and Apple meta tags to the pot detail page
- Add tip to the help page
