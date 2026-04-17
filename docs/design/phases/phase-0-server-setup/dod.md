# Phase 0 — Definition of Done

- [x] Hetzner VPS is provisioned and running Ubuntu 24.04 LTS
- [x] SSH access works for both `root` and `potdev` users
- [x] Firewall is configured (only ports 22, 80, 443 open)
- [x] `pot.respobit.eu` DNS A record points to the server IP
- [x] nginx is installed and serving a static "Hello" page over HTTP at `pot.respobit.eu`
- [x] SSL certificate is issued for `pot.respobit.eu` and auto-renewal is configured
- [x] `pot.respobit.eu` is reachable over HTTPS in a mobile browser
- [x] HTTP requests are redirected to HTTPS
- [x] Python 3.12 is installed and available system-wide
- [x] gunicorn is installed in a virtual environment
- [x] A minimal Python "Hello" app served by gunicorn is accessible via nginx at `pot.respobit.eu`
