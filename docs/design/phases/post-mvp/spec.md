# Post-MVP

> Features planned after the MVP is live.

## Backlog

- Auto-delete pots with no activity for one year
- Docker container for simplified deployment
- Bot command support for placeholder members (`/paid`, `/split` by display name)
- Send Telegram notifications asynchronously so the web request doesn't block on bot API calls
- Per-user appearance settings: font size, compact/comfortable spacing, theme (light/dark persisted server-side), show/hide checked list items by default
- Receipt photo attachments on drops — single optional photo per drop, captured from camera or file picker (`<input type="file" accept="image/*" capture="environment">`). DB stores only the file path (FileField). Two storage options: (a) filesystem on VPS — simplest, zero cost, but needs media backup alongside db.sqlite3 and disk space monitoring; (b) object storage (Cloudflare R2 / Backblaze B2) — more robust, negligible cost at this scale, adds a dependency. Either way: nginx `client_max_body_size` must be raised (phone photos are 3–10 MB), a `/media/` location block added to nginx config, and optionally Pillow used for server-side resize/thumbnail. No significant DB load — the file is on disk. Estimated effort: ~half a day for filesystem + single photo; add another half day for thumbnails or cloud storage.
