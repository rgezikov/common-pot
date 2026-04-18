"""
Common Pot Telegram bot.

Run with: python bot.py
Requires COMPOT_TELEGRAM_BOT_TOKEN in environment.
"""
import datetime
import logging
import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commonpot.settings')
django.setup()

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from pots.models import Pot, Member, Drop, Split
from pots.splits import calculate_splits
from pots.balances import calculate_balances, calculate_settlements
from pots.bot_parser import parse_drop_command
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SITE_URL = 'https://pot.respobit.eu'


# --- Sync DB helpers (called via sync_to_async) ---

def _get_pot_for_chat_sync(chat_id: int):
    """Return the Pot linked to this chat, or None."""
    return Pot.objects.filter(telegram_chat_id=chat_id).first()


def _create_pot_for_chat_sync(chat) -> Pot:
    """Create a new Pot linked to this chat."""
    return Pot.objects.create(
        name=chat.title or f'Chat {chat.id}',
        telegram_chat_id=chat.id,
    )


def _link_pot_to_chat_sync(token_str: str, chat_id: int):
    """
    Link an existing pot (by invite token or full invite URL) to this chat.
    Returns (pot, error_message). error_message is None on success.
    """
    # Extract UUID from full URL if needed
    import re
    m = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', token_str, re.I)
    if m:
        token_str = m.group(0)
    try:
        token = uuid.UUID(token_str)
    except ValueError:
        return None, "Invalid token format."
    try:
        pot = Pot.objects.get(invite_token=token)
    except Pot.DoesNotExist:
        return None, "No pot found with that invite token."
    if pot.telegram_chat_id and pot.telegram_chat_id != chat_id:
        return None, "This pot is already linked to a different group."
    pot.telegram_chat_id = chat_id
    pot.save(update_fields=['telegram_chat_id'])
    return pot, None


def _get_or_create_member_sync(pot: Pot, tg_user) -> Member:
    name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip() or tg_user.username or str(tg_user.id)
    member, created = Member.objects.get_or_create(
        pot=pot,
        telegram_user_id=tg_user.id,
        defaults={
            'name': name,
            'telegram_username': (tg_user.username or '').lower(),
        },
    )
    if not created and tg_user.username and member.telegram_username != tg_user.username.lower():
        member.telegram_username = tg_user.username.lower()
        member.save(update_fields=['telegram_username'])
    return member


def _get_members_sync(pot: Pot):
    return list(pot.members.all())


def _get_balances_sync(pot: Pot):
    members = list(pot.members.all())
    drops = list(pot.drops.select_related('paid_by').prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)
    return balances, member_names, settlements


def _create_drop_sync(pot, description, amount, paid_by, splits):
    drop = Drop.objects.create(
        pot=pot,
        description=description,
        amount=amount,
        paid_by=paid_by,
        date=datetime.date.today(),
        source=Drop.SOURCE_TELEGRAM,
    )
    for member_id, share in splits.items():
        Split.objects.create(drop=drop, member_id=member_id, amount=share)
    return drop


# --- Handlers ---

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help — list available commands."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "*Common Pot commands*\n\n"
            "/pot new — create a new pot for this group\n"
            "/pot <invite\\_token> — link an existing pot\n"
            "/link — get the web app link\n"
            "/drop <amount> <description> — log an expense\n"
            "/balance — show member balances\n"
            "/settle — show settlement suggestions"
        ),
        parse_mode='Markdown',
    )

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot added to a group — show instructions."""
    bot_id = context.bot.id
    for new_member in update.message.new_chat_members:
        if new_member.id == bot_id:
            await update.message.reply_text(
                "👋 Common Pot is here!\n\n"
                "To get started:\n"
                "• /pot new — create a new pot for this group\n"
                "• /pot <invite\\_url> — link an existing pot from the web app\n\n"
                "Once linked:\n"
                "• /link — get the web app invite link\n"
                "• /drop — log an expense",
                parse_mode='Markdown',
            )


async def cmd_pot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pot new | /pot <invite_token>"""
    if update.effective_chat.type == 'private':
        await update.message.reply_text("Use /pot in a group chat.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage:\n/pot new — create a new pot\n/pot <invite\\_token> — link existing pot",
            parse_mode='Markdown',
        )
        return

    chat = update.effective_chat
    subcommand = args[0].lower()

    if subcommand == 'new':
        existing = await sync_to_async(_get_pot_for_chat_sync)(chat.id)
        if existing:
            invite_url = f"{SITE_URL}/join/{existing.invite_token}/"
            await update.message.reply_text(
                f"This group is already linked to pot *{existing.name}*.\n[Join the web app]({invite_url})",
                parse_mode='Markdown',
            )
            return
        pot = await sync_to_async(_create_pot_for_chat_sync)(chat)
        invite_url = f"{SITE_URL}/join/{pot.invite_token}/"
        await update.message.reply_text(
            f"✅ Pot *{pot.name}* created!\n"
            f"[Join the web app]({invite_url})\n\n"
            f"Use /link to get the invite link, /drop to log expenses.",
            parse_mode='Markdown',
        )
    else:
        pot, error = await sync_to_async(_link_pot_to_chat_sync)(args[0], chat.id)
        if error:
            await update.message.reply_text(f"❌ {error}")
            return
        invite_url = f"{SITE_URL}/join/{pot.invite_token}/"
        await update.message.reply_text(
            f"✅ Linked to pot *{pot.name}*!\n"
            f"[Join the web app]({invite_url})\n\n"
            f"Use /link to get the invite link, /drop to log expenses.",
            parse_mode='Markdown',
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start or /invite — reply with invite link."""
    if update.effective_chat.type == 'private':
        await update.message.reply_text("Add me to a group chat to start tracking expenses!")
        return
    pot = await sync_to_async(_get_pot_for_chat_sync)(update.effective_chat.id)
    if not pot:
        await update.message.reply_text(
            "No pot linked yet. Use /pot new or /pot <invite\\_token>.",
            parse_mode='Markdown',
        )
        return
    join_url = f"{SITE_URL}/join/{pot.invite_token}/"
    open_url = f"{SITE_URL}/pot/{pot.invite_token}/"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Pot: *{pot.name}*\n[Open pot]({open_url}) · [Join pot]({join_url})",
        parse_mode='Markdown',
    )


async def cmd_drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/drop <amount> <description> [@payer]"""
    if update.effective_chat.type == 'private':
        await update.message.reply_text("Use /drop in a group chat.")
        return

    pot = await sync_to_async(_get_pot_for_chat_sync)(update.effective_chat.id)
    if not pot:
        await update.message.reply_text(
            "No pot linked yet. Use /pot new or /pot <invite\\_token>.",
            parse_mode='Markdown',
        )
        return

    text = ' '.join(context.args) if context.args else ''
    try:
        parsed = parse_drop_command(text)
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {e}\n\nUsage: /drop <amount> <description> [@payer]"
        )
        return

    members = await sync_to_async(_get_members_sync)(pot)
    if not members:
        await update.message.reply_text("No members in this pot yet. Join via the web app first.")
        return

    sender = await sync_to_async(_get_or_create_member_sync)(pot, update.effective_user)
    paid_by = sender
    if parsed['payer_username']:
        bot_username = (await context.bot.get_me()).username.lower()
        if parsed['payer_username'] == bot_username:
            await update.message.reply_text("❌ The bot cannot be the payer. Specify a member or omit @payer to use yourself.")
            return
        match = next(
            (m for m in members if m.telegram_username == parsed['payer_username']),
            None,
        )
        if match:
            paid_by = match
        else:
            await update.message.reply_text(
                f"❌ @{parsed['payer_username']} is not a member of this pot."
            )
            return

    weights = {m.id: Decimal('1') for m in members}
    splits = calculate_splits(parsed['amount'], weights)

    await sync_to_async(_create_drop_sync)(pot, parsed['description'], parsed['amount'], paid_by, splits)

    share = splits.get(sender.id, Decimal('0'))
    await update.message.reply_text(
        f"✅ *{parsed['description']}* — {parsed['amount']}\n"
        f"Paid by: {paid_by.name}\n"
        f"Split equally among {len(splits)} members ({share} each)",
        parse_mode='Markdown',
    )


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/balance — show per-member balance summary."""
    if update.effective_chat.type == 'private':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Use /balance in a group chat.")
        return
    pot = await sync_to_async(_get_pot_for_chat_sync)(update.effective_chat.id)
    if not pot:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No pot linked. Use /pot new or /pot <invite\\_url>.", parse_mode='Markdown')
        return
    balances, member_names, _ = await sync_to_async(_get_balances_sync)(pot)
    if not balances:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No members in this pot yet.")
        return
    rows = sorted(balances.items(), key=lambda x: x[1]['balance'], reverse=True)
    lines = [f"*{pot.name}* — Balances\n"]
    for mid, v in rows:
        sign = '+' if v['balance'] > 0 else ''
        lines.append(f"{member_names[mid]}: {sign}{v['balance']} (paid {v['paid']}, owed {v['owed']})")
    await context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(lines), parse_mode='Markdown')


async def cmd_settle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/settle — show settlement suggestions."""
    if update.effective_chat.type == 'private':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Use /settle in a group chat.")
        return
    pot = await sync_to_async(_get_pot_for_chat_sync)(update.effective_chat.id)
    if not pot:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No pot linked. Use /pot new or /pot <invite\\_url>.", parse_mode='Markdown')
        return
    _, _, settlements = await sync_to_async(_get_balances_sync)(pot)
    if not settlements:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ All settled up!")
        return
    lines = [f"*{pot.name}* — Settlements\n"]
    for s in settlements:
        lines.append(f"{s['from_name']} pays {s['to_name']}: {s['amount']}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(lines), parse_mode='Markdown')


def main():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("COMPOT_TELEGRAM_BOT_TOKEN is not set")

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('pot', cmd_pot))
    app.add_handler(CommandHandler('link', cmd_start))
    app.add_handler(CommandHandler('drop', cmd_drop))
    app.add_handler(CommandHandler('balance', cmd_balances))
    app.add_handler(CommandHandler('settle', cmd_settle))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == '__main__':
    main()
