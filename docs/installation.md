# Installation

Server installation guide for Ubuntu 24.04 LTS.

The Telegram bot is optional — the web app works standalone without it.

## Prerequisites

- A VPS or server with Ubuntu 24.04 LTS
- A domain name with an A record pointing to the server's IP

## Step 1 — Server setup

Provision the server, configure the firewall, set up nginx with HTTPS, and install Python. Follow [`docs/design/phases/phase-0-server-setup/runbook.md`](design/phases/phase-0-server-setup/runbook.md) for step-by-step instructions.

Assumed user: `potdev`, app directory: `~/app`.

## Step 2 — Deploy the application

SSH into the server and clone the repo:

```bash
ssh potdev@<your-server>
git clone git@github.com:rgezikov/common-pot.git ~/app
cd ~/app
```

Install uv if not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Create the virtual environment and install dependencies:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

Create `~/app/.env.local`:

```
COMPOT_SECRET_KEY=<strong random key>
# Optional — only needed if running the Telegram bot
COMPOT_TELEGRAM_BOT_TOKEN=<bot token>
COMPOT_TELEGRAM_BOT_NAME=<bot username>
```

- **`COMPOT_SECRET_KEY`** — Django's secret key for cryptographic signing. Generate one with:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **`COMPOT_TELEGRAM_BOT_TOKEN`** — the token issued by [@BotFather](https://t.me/BotFather) when you create a bot (`/newbot`). Optional.
- **`COMPOT_TELEGRAM_BOT_NAME`** — the bot's username without the `@`, e.g. `common_pot_bot`. Optional.

Run migrations and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## systemd service — web app

Copy the service file from the repo and install it:

```bash
sudo cp ~/app/deploy/commonpot.service /etc/systemd/system/commonpot.service
```

## systemd service — bot (optional)

Skip this section if you are not using the Telegram bot.

```bash
sudo cp ~/app/deploy/commonpot-bot.service /etc/systemd/system/commonpot-bot.service
```

Enable and start the services:

```bash
sudo systemctl daemon-reload
# Web app only:
sudo systemctl enable commonpot && sudo systemctl start commonpot
# Also enable the bot (if using it):
sudo systemctl enable commonpot-bot && sudo systemctl start commonpot-bot
```

## nginx config

`/etc/nginx/sites-available/default` — inside the `server` block for your domain:

```nginx
location /static/ {
    alias /home/potdev/app/staticfiles/;
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Reload nginx:

```bash
sudo systemctl reload nginx
```

## Updating

```bash
cd ~/app
git pull
source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart commonpot
sudo systemctl restart commonpot-bot  # if running the bot
```
