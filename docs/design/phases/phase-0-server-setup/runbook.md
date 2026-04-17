# Phase 0 — Runbook: Server Setup

## Prerequisites

- Hetzner account created
- SSH key pair available on your local machine (`~/.ssh/id_rsa.pub` or similar)
- Access to hostaan.fi DNS management for `respobit.eu`

---

## Step 1 — Provision Hetzner VPS

1. Log in to [Hetzner Cloud Console](https://console.hetzner.cloud)
2. Create a new project (e.g. `common-pot`)
3. Add a new server:
   - **Image**: Ubuntu 24.04
   - **Type**: CX23 (2 vCPU, 4GB RAM, 40GB disk)
   - **Location**: Helsinki
   - **SSH key**: add your public key
   - **Name**: `common-pot`
4. Note the server's public IP address

---

## Step 2 — Add DNS A Record

1. Log in to hostaan.fi
2. Go to DNS management for `respobit.eu`
3. Add an A record:
   - **Host**: `pot`
   - **Value**: `<server IP>`
   - **TTL**: 300 (or default)
4. Wait for DNS propagation (up to 10 minutes)
5. Verify: `ping pot.respobit.eu` should resolve to your server IP

---

## Step 3 — Initial Server Login & Hardening

SSH into the server as root:

```bash
ssh root@pot.respobit.eu
```

Update the system:

```bash
apt update && apt upgrade -y
```

Create a non-root user:

```bash
adduser potdev
usermod -aG sudo potdev
```

Copy SSH key to new user:

```bash
rsync --archive --chown=potdev:potdev ~/.ssh /home/potdev
```

Disable password login and root login via SSH:

```bash
nano /etc/ssh/sshd_config
```

Set these values:

```
PermitRootLogin no
PasswordAuthentication no
```

Restart SSH:

```bash
systemctl restart ssh
```

Open a new terminal and verify login as new user before closing the root session:

```bash
ssh potdev@pot.respobit.eu
```

---

## Step 4 — Configure Firewall

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
ufw status
```

---

## Step 5 — Install nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

Create a simple Hello page:

```bash
sudo nano /var/www/html/index.html
```

Content:

```html
<!DOCTYPE html>
<html>
  <head><title>Common Pot</title></head>
  <body><h1>Hello from Common Pot</h1></body>
</html>
```

Verify: open `http://pot.respobit.eu` in a browser — you should see the Hello page.

---

## Step 6 — Install SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d pot.respobit.eu
```

Follow the prompts:
- Enter your email address
- Agree to terms of service
- Choose to redirect HTTP to HTTPS (option 2)

Verify auto-renewal:

```bash
sudo systemctl status certbot.timer
```

Verify: open `https://pot.respobit.eu` in a mobile browser — should show the Hello page over HTTPS.

---

## Step 7 — Install Python 3.12 and gunicorn

Python 3.12 is available in Ubuntu 24.04 default repos:

```bash
sudo apt install python3.12 python3.12-venv python3-pip -y
python3 --version  # should print Python 3.12.x
```

Create app directory and virtual environment:

```bash
mkdir -p ~/app
cd ~/app
python3 -m venv .venv
source .venv/bin/activate
pip install gunicorn
```

---

## Step 8 — Serve a Minimal Python App via gunicorn + nginx

Create a minimal WSGI app:

```bash
nano ~/app/hello.py
```

Content:

```python
def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"<h1>Hello from gunicorn</h1>"]
```

Test gunicorn manually:

```bash
cd ~/app
source .venv/bin/activate
gunicorn --bind 127.0.0.1:8000 hello:application
```

Configure nginx to proxy to gunicorn. Edit the nginx config:

```bash
sudo nano /etc/nginx/sites-available/default
```

Replace the `location /` block with:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Reload nginx:

```bash
sudo systemctl reload nginx
```

Verify: open `https://pot.respobit.eu` — should show "Hello from gunicorn".

---

## Step 9 — Verify DoD

Go through `dod.md` and confirm all checkboxes are met.
