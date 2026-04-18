"""
Send notifications to Telegram group chats from the web UI.
Uses the Bot API directly via httpx (sync) — no bot process needed.
"""
import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

SITE_URL = 'https://pot.respobit.eu'


def notify_drop_added(pot, drop):
    """Post a message to the pot's linked group chat when a drop is added via web UI."""
    if not pot.telegram_chat_id:
        return
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return

    pot_url = f"{SITE_URL}/pot/{pot.invite_token}/"
    text = (
        f"💧 New drop in *{pot.name}*\n"
        f"{drop.description} — {drop.amount}\n"
        f"Paid by: {drop.paid_by.name}\n"
        f"[Open pot]({pot_url})"
    )
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={'chat_id': pot.telegram_chat_id, 'text': text, 'parse_mode': 'Markdown'},
            timeout=5,
        )
    except Exception as e:
        logger.warning("Failed to send Telegram notification: %s", e)
