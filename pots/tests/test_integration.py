"""
Integration tests: realistic pot with many members and drops.

Tests correctness of balance calculation, settlement algorithm,
and HTTP responses for all main views.
"""
import random
import uuid
from decimal import Decimal
import pytest
from django.test import Client
from pots.models import Pot, Member, Drop, Split
from pots.balances import calculate_balances, calculate_settlements
from pots.splits import calculate_splits


SEED = 42
NUM_MEMBERS = 30
NUM_DROPS = 100


@pytest.fixture
def big_pot(db):
    """Pot with 30 members and 100 drops, deterministically random."""
    rng = random.Random(SEED)

    pot = Pot.objects.create(name='Integration Test Pot', description='Auto-generated')
    members = [
        Member.objects.create(
            pot=pot,
            telegram_user_id=1000 + i,
            name=f'Member {i:02d}',
        )
        for i in range(NUM_MEMBERS)
    ]

    for _ in range(NUM_DROPS):
        amount = Decimal(str(round(rng.uniform(5, 500), 2)))
        payer = rng.choice(members)

        # Random subset of members involved (at least 2)
        k = rng.randint(2, NUM_MEMBERS)
        involved = rng.sample(members, k)
        weights = {m.id: Decimal('1') for m in involved}
        splits = calculate_splits(amount, weights)

        drop = Drop.objects.create(
            pot=pot,
            description=f'Drop {_}',
            amount=amount,
            paid_by=payer,
            date='2026-01-01',
        )
        for member_id, share in splits.items():
            Split.objects.create(drop=drop, member_id=member_id, amount=share)

    return pot, members


# --- Correctness tests ---

def test_balances_sum_to_zero(big_pot):
    pot, members = big_pot
    drops = list(pot.drops.prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    total = sum(v['balance'] for v in balances.values())
    assert abs(total) <= Decimal('0.10'), f"Balances sum to {total}, expected ~0"


def test_paid_equals_drop_total(big_pot):
    pot, members = big_pot
    drops = list(pot.drops.prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    total_paid = sum(v['paid'] for v in balances.values())
    total_drops = sum(d.amount for d in drops)
    assert total_paid == total_drops


def test_owed_equals_drop_total(big_pot):
    pot, members = big_pot
    drops = list(pot.drops.prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    total_owed = sum(v['owed'] for v in balances.values())
    total_drops = sum(d.amount for d in drops)
    assert total_owed == total_drops


def test_settlements_clear_all_balances(big_pot):
    pot, members = big_pot
    drops = list(pot.drops.prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)

    # Apply settlements and check residuals
    net = {mid: v['balance'] for mid, v in balances.items()}
    name_to_id = {v: k for k, v in member_names.items()}
    for s in settlements:
        debtor = name_to_id[s['from_name']]
        creditor = name_to_id[s['to_name']]
        net[debtor] += s['amount']
        net[creditor] -= s['amount']

    for mid, remaining in net.items():
        assert abs(remaining) <= Decimal('0.01'), \
            f"{member_names[mid]} still has residual {remaining} after settlement"


def test_settlement_count_at_most_n_minus_1(big_pot):
    pot, members = big_pot
    drops = list(pot.drops.prefetch_related('splits').all())
    balances = calculate_balances(members, drops)
    member_names = {m.id: m.name for m in members}
    settlements = calculate_settlements(balances, member_names)
    assert len(settlements) <= NUM_MEMBERS - 1


# --- HTTP view tests ---

@pytest.fixture
def auth_client(big_pot):
    pot, members = big_pot
    client = Client()
    session = client.session
    session['telegram_user'] = {
        'id': members[0].telegram_user_id,
        'first_name': members[0].name,
        'last_name': '',
        'username': '',
    }
    session.save()
    return client, pot, members


def test_home_view(auth_client):
    client, pot, members = auth_client
    response = client.get('/')
    assert response.status_code == 200


def test_pot_detail_view(auth_client):
    client, pot, members = auth_client
    response = client.get(f'/pot/{pot.invite_token}/')
    assert response.status_code == 200


def test_drop_list_on_pot_detail(auth_client):
    client, pot, members = auth_client
    response = client.get(f'/pot/{pot.invite_token}/')
    assert response.status_code == 200
    assert NUM_DROPS == pot.drops.count()


def test_drop_detail_view(auth_client):
    client, pot, members = auth_client
    drop = pot.drops.first()
    response = client.get(f'/pot/{pot.invite_token}/drop/{drop.id}/')
    assert response.status_code == 200


def test_add_drop_view_get(auth_client):
    client, pot, members = auth_client
    response = client.get(f'/pot/{pot.invite_token}/drop/new/')
    assert response.status_code == 200


def test_add_drop_post(auth_client):
    client, pot, members = auth_client
    payer = members[1]
    response = client.post(f'/pot/{pot.invite_token}/drop/new/', {
        'description': 'Integration test drop',
        'amount': '99.00',
        'date': '2026-04-01',
        'paid_by': payer.id,
    })
    assert response.status_code == 302
    assert pot.drops.filter(description='Integration test drop').exists()
