# Development

Local development setup.

## Prerequisites

- Linux, macOS, or WSL2 on Windows
- [uv](https://github.com/astral-sh/uv) — Python version and package manager
- A Telegram bot token (create one via [@BotFather](https://t.me/BotFather))

## Setup

Install uv if not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Clone the repo and install dependencies:

```bash
git clone git@github.com:rgezikov/common-pot.git
cd common-pot

uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

Create `.env.local` in the project root:

```
COMPOT_DEBUG=True
COMPOT_TELEGRAM_BOT_TOKEN=123456:ABC-your-bot-token
COMPOT_TELEGRAM_BOT_NAME=your_bot_username
```

- **`COMPOT_DEBUG=True`** — enables Django debug mode (required for local dev).
- **`COMPOT_TELEGRAM_BOT_TOKEN`** — the token issued by [@BotFather](https://t.me/BotFather) when you create a bot (`/newbot`).
- **`COMPOT_TELEGRAM_BOT_NAME`** — the bot's username without the `@`, e.g. `common_pot_bot`.

Run migrations and start the dev server:

```bash
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## Run the bot

```bash
python bot.py
```

## Run tests

```bash
pytest
```
