"""
Parse /drop command arguments from Telegram bot messages.

Syntax: /drop <amount> <description> [@payer]

- amount: first token, numeric
- description: everything after amount, up to optional @payer at the end
  may be wrapped in single or double quotes
- @payer: optional last token starting with @
"""
import re
from decimal import Decimal, InvalidOperation


def parse_drop_command(text: str) -> dict:
    """
    Parse /drop command text (without the /drop prefix).

    Returns dict with keys: amount, description, payer_username (or None)
    Raises ValueError with a user-friendly message on parse error.
    """
    text = text.strip()
    if not text:
        raise ValueError("Usage: /drop <amount> <description> [@payer]")

    # Split off amount (first token)
    parts = text.split(None, 1)
    amount_str = parts[0]
    rest = parts[1].strip() if len(parts) > 1 else ''

    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {amount_str!r}")

    if not rest:
        raise ValueError("Description is required")

    # Extract optional @payer from the end
    payer_username = None
    payer_match = re.search(r'\s+@(\w+)\s*$', rest)
    if payer_match:
        payer_username = payer_match.group(1).lower()
        rest = rest[:payer_match.start()].strip()

    # Strip optional quotes from description
    if (rest.startswith('"') and rest.endswith('"')) or \
       (rest.startswith("'") and rest.endswith("'")):
        rest = rest[1:-1].strip()

    if not rest:
        raise ValueError("Description is required")

    return {
        'amount': amount,
        'description': rest,
        'payer_username': payer_username,
    }
