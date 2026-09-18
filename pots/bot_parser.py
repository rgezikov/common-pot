"""
Parse /drop command arguments from Telegram bot messages.

Syntax:
  /drop <amount> [description] [/paid @username] [/split @username[:weight] [, @username[:weight] ...]] [/settlement]

- amount: first token, numeric
- description: words before any /paid, /split, or /settlement marker
- /paid @username   — payer by Telegram username
- /split @username[:weight] [, @username[:weight] ...]
                    — custom split; items separated by commas; weight
                      defaults to 1 if omitted; members not listed are
                      excluded from this drop
- /settlement       — mark as a settlement/repayment: still counts toward
                      balances, but excluded from the Spending total
                      (distinct from the /settle command, which shows
                      suggested transfers)
- Members must have a Telegram username to be referenced in /paid or /split
- Legacy: @username as the last description token is accepted as payer

Examples:
  /drop 120 dinner
  /drop 120 dinner /paid @alice
  /drop 102 payback /paid @roman /split @roman:1, @rgezikov:2
  /drop 120 dinner /split @alice:1, @bob:2
  /drop 50 payback /paid @bob /split @alice /settlement
"""
import re
import shlex
from decimal import Decimal, InvalidOperation


def parse_drop_command(text: str) -> dict:
    """
    Parse /drop command text (without the /drop prefix).

    Returns dict with keys: amount, tokens (list of str)
    Raises ValueError with a user-friendly message on parse error.
    """
    text = text.strip()
    if not text:
        raise ValueError(
            "Usage: /drop <amount> [description] [/paid @user] [/split @user[:weight], ...] [/settlement]"
        )

    # Ensure /paid, /split, and /settlement are always separate tokens even without a leading space
    text = re.sub(r'(\S)(/paid\b|/split\b|/settlement\b)', r'\1 \2', text)
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()

    amount_str = tokens[0]
    remaining = list(tokens[1:])

    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {amount_str!r}")

    if not remaining:
        raise ValueError("Description is required")

    return {
        'amount': amount,
        'tokens': remaining,
    }


def resolve_member_specs(tokens: list, members) -> tuple:
    """
    Parse tokens into (description, weights_or_none, payer_member_or_none, is_settlement).

    Recognises three markers:
      /paid:<name>  — payer; name extends (with spaces) to next marker
      /split        — split specs follow as name:weight pairs
      /settlement   — standalone flag; marks the drop as a settlement/repayment

    Legacy: a lone @username at the end of the description section = payer.

    Returns:
      description    — str
      weights        — {member_id: Decimal} or None (None = equal split among all)
      payer_member   — Member or None
      is_settlement  — bool
    """
    member_by_username = {m.telegram_username.lower(): m for m in members if m.telegram_username}

    def lookup(key):
        key = key.lstrip('@').lower()
        return member_by_username.get(key)

    # Split tokens into sections based on /paid: and /split markers
    description_tokens = []
    paid_tokens = []
    split_tokens = []
    current = 'description'
    is_settlement = False

    for token in tokens:
        tl = token.lower()
        if tl == '/paid':
            current = 'paid'
        elif tl == '/split':
            current = 'split'
        elif tl == '/settlement':
            is_settlement = True
        else:
            if current == 'description':
                description_tokens.append(token)
            elif current == 'paid':
                paid_tokens.append(token)
            else:
                split_tokens.append(token)

    # Legacy @username at end of description
    payer_member = None
    if description_tokens and re.match(r'^@\w+$', description_tokens[-1]):
        payer_member = lookup(description_tokens.pop())

    # Payer from /paid: section
    if paid_tokens and payer_member is None:
        payer_member = lookup(' '.join(paid_tokens))

    description = ' '.join(description_tokens)

    # Resolve split specs — join tokens, split on commas, each item is name:weight
    if not split_tokens:
        return description, None, payer_member, is_settlement

    split_str = ' '.join(split_tokens)
    items = [item.strip() for item in split_str.split(',') if item.strip()]

    weights = {}
    for item in items:
        if ':' in item:
            name_part, _, weight_str = item.rpartition(':')
            name_part = name_part.strip()
            try:
                weight = Decimal(weight_str.strip())
                if weight < 0:
                    continue
            except InvalidOperation:
                continue
        else:
            name_part = item.strip()
            weight = Decimal('1')
        member = lookup(name_part)
        if member is not None:
            weights[member.id] = weight

    return description, weights if weights else None, payer_member, is_settlement
