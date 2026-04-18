from decimal import Decimal


def calculate_balances(members, drops):
    """
    Calculate each member's paid, owed, and net balance.

    Args:
        members: iterable of Member objects
        drops: iterable of Drop objects with prefetched splits and paid_by

    Returns:
        dict of {member_id: {'paid': Decimal, 'owed': Decimal, 'balance': Decimal}}
    """
    data = {m.id: {'paid': Decimal('0'), 'owed': Decimal('0')} for m in members}

    for drop in drops:
        if drop.paid_by_id in data:
            data[drop.paid_by_id]['paid'] += drop.amount
        for split in drop.splits.all():
            if split.member_id in data:
                data[split.member_id]['owed'] += split.amount

    for v in data.values():
        v['balance'] = v['paid'] - v['owed']

    return data


def calculate_settlements(balances, member_names):
    """
    Generate a minimal set of transfers to settle all balances.

    Uses a greedy algorithm: repeatedly match the largest debtor
    with the largest creditor.

    Args:
        balances: dict of {member_id: Decimal balance}
        member_names: dict of {member_id: str name}

    Returns:
        list of dicts: [{'from_name': str, 'to_name': str, 'amount': Decimal}, ...]
    """
    ZERO = Decimal('0')
    CENT = Decimal('0.01')

    # Work with mutable copies, ignore already-settled members
    b = {k: v['balance'] for k, v in balances.items() if abs(v['balance']) >= CENT}

    settlements = []

    while True:
        debtors = sorted([(v, k) for k, v in b.items() if v < -CENT])   # most negative first
        creditors = sorted([(v, k) for k, v in b.items() if v > CENT], reverse=True)  # most positive first

        if not debtors or not creditors:
            break

        debt_amount, debtor_id = debtors[0]
        credit_amount, creditor_id = creditors[0]

        transfer = min(-debt_amount, credit_amount).quantize(CENT)

        settlements.append({
            'from_name': member_names[debtor_id],
            'to_name': member_names[creditor_id],
            'amount': transfer,
        })

        b[debtor_id] += transfer
        b[creditor_id] -= transfer

        if abs(b[debtor_id]) < CENT:
            del b[debtor_id]
        if abs(b[creditor_id]) < CENT:
            del b[creditor_id]

    return settlements
