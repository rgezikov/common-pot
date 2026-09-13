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
from pots.models import Pot, CompotUser, Member, Drop, Split
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
            user=CompotUser.objects.create(
                telegram_user_id=1000 + i,
                name=f'Member {i:02d}',
            ),
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


def test_add_drop_post_comma_decimal_amount(auth_client):
    """iPhones with a comma-decimal locale send '99,00' instead of '99.00'."""
    client, pot, members = auth_client
    payer = members[1]
    response = client.post(f'/pot/{pot.invite_token}/drop/new/', {
        'description': 'Comma amount drop',
        'amount': '99,00',
        'date': '2026-04-01',
        'paid_by': payer.id,
    })
    assert response.status_code == 302
    drop = pot.drops.get(description='Comma amount drop')
    assert drop.amount == Decimal('99.00')


def test_add_drop_form_weight_defaults_are_real_values(auth_client):
    """Default weights must be actual input values, not placeholders — otherwise
    zeroing every other member's field silently does nothing, since an untouched
    placeholder is never submitted and reads back as 0. Blank is fine (it is a
    real, submitted empty value that the "Split equally" button fills to 1)."""
    client, pot, members = auth_client
    response = client.get(f'/pot/{pot.invite_token}/drop/new/')
    content = response.content.decode()
    assert 'placeholder=' not in content
    for member in members:
        assert f'name="weight_{member.id}" min="0" step="any"\n                    value=""' in content


def test_add_drop_post_zeroing_others_directs_full_amount_to_one_member(auth_client):
    client, pot, members = auth_client
    payer = members[0]
    recipient = members[1]
    data = {
        'description': 'Single recipient drop',
        'amount': '50.00',
        'date': '2026-04-01',
        'paid_by': payer.id,
    }
    for member in members:
        data[f'weight_{member.id}'] = '1' if member.id == recipient.id else '0'
    response = client.post(f'/pot/{pot.invite_token}/drop/new/', data)
    assert response.status_code == 302
    drop = pot.drops.get(description='Single recipient drop')
    splits = list(drop.splits.all())
    assert len(splits) == 1
    assert splits[0].member_id == recipient.id
    assert splits[0].amount == Decimal('50.00')
