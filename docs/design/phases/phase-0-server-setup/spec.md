# Phase 0 — Server Setup

> Get the server running and reachable from the internet.

## Tasks

- Provision Hetzner VPS with Ubuntu 24.04 LTS
- Basic server hardening (SSH key auth, disable password login, firewall)
- Install nginx and serve a static "Hello" page over HTTP
- Add DNS A record: `pot.respobit.eu` → server IP
- Install SSL certificate via Let's Encrypt / certbot for `pot.respobit.eu` — serve over HTTPS
- Install Python 3.12 and gunicorn
- Confirm gunicorn can serve a minimal Python app behind nginx
