# Phase 0 — Definition of Done

- [ ] Hetzner VPS is provisioned and running Ubuntu 24.04 LTS
- [ ] SSH access works using key-based authentication only (password login disabled)
- [ ] Firewall is configured (only ports 22, 80, 443 open)
- [ ] `pot.respobit.eu` DNS A record points to the server IP
- [ ] nginx is installed and serving a static "Hello" page over HTTP at `pot.respobit.eu`
- [ ] SSL certificate is issued for `pot.respobit.eu` and auto-renewal is configured
- [ ] `pot.respobit.eu` is reachable over HTTPS in a mobile browser
- [ ] HTTP requests are redirected to HTTPS
- [ ] Python 3.12 is installed and available system-wide
- [ ] gunicorn is installed in a virtual environment
- [ ] A minimal Python "Hello" app served by gunicorn is accessible via nginx at `pot.respobit.eu`
