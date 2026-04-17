from decimal import Decimal, ROUND_DOWN


def calculate_splits(amount: Decimal, weights: dict) -> dict:
    """
    Calculate split amounts from weights.

    Args:
        amount: total drop amount
        weights: dict of {member_id: weight} — members with weight <= 0 are excluded

    Returns:
        dict of {member_id: Decimal amount} for members with weight > 0

    Raises:
        ValueError: if weights are all zero or negative
    """
    active = {k: Decimal(str(v)) for k, v in weights.items() if Decimal(str(v)) > 0}
    if not active:
        raise ValueError("At least one member must have a positive weight")

    total_weight = sum(active.values())
    cent = Decimal('0.01')

    shares = {}
    allocated = Decimal('0')
    members = list(active.keys())

    for member_id in members[:-1]:
        share = (active[member_id] / total_weight * amount).quantize(cent, rounding=ROUND_DOWN)
        shares[member_id] = share
        allocated += share

    # Last member gets the remainder to ensure total sums exactly to amount
    shares[members[-1]] = amount - allocated

    return shares
