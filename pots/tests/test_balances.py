from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from pots.balances import calculate_balances, calculate_settlements


# --- Helpers to build fake model objects ---

def make_member(id, name):
    m = MagicMock()
    m.id = id
    m.name = name
    return m


def make_split(member_id, amount):
    s = MagicMock()
    s.member_id = member_id
    s.amount = Decimal(str(amount))
    return s


def make_drop(paid_by_id, amount, splits):
    d = MagicMock()
    d.paid_by_id = paid_by_id
    d.amount = Decimal(str(amount))
    d.splits.all.return_value = splits
    return d


# --- Balance tests ---

def test_single_payer_two_members_equal():
    alice, bob = make_member(1, 'Alice'), make_member(2, 'Bob')
    drop = make_drop(1, '100.00', [
        make_split(1, '50.00'),
        make_split(2, '50.00'),
    ])
    balances = calculate_balances([alice, bob], [drop])
    assert balances[1] == Decimal('50.00')   # Alice paid 100, owes 50 → +50
    assert balances[2] == Decimal('-50.00')  # Bob paid 0, owes 50 → -50


def test_two_drops_different_payers():
    alice, bob = make_member(1, 'Alice'), make_member(2, 'Bob')
    drop1 = make_drop(1, '60.00', [make_split(1, '30.00'), make_split(2, '30.00')])
    drop2 = make_drop(2, '40.00', [make_split(1, '20.00'), make_split(2, '20.00')])
    balances = calculate_balances([alice, bob], [drop1, drop2])
    assert balances[1] == Decimal('10.00')   # paid 60, owes 50
    assert balances[2] == Decimal('-10.00')  # paid 40, owes 30... wait: paid 40, owes 50 → -10


def test_zero_balance_when_everyone_pays_own_share():
    alice, bob = make_member(1, 'Alice'), make_member(2, 'Bob')
    drop1 = make_drop(1, '50.00', [make_split(1, '50.00')])
    drop2 = make_drop(2, '50.00', [make_split(2, '50.00')])
    balances = calculate_balances([alice, bob], [drop1, drop2])
    assert balances[1] == Decimal('0.00')
    assert balances[2] == Decimal('0.00')


def test_no_drops_all_zero():
    alice, bob = make_member(1, 'Alice'), make_member(2, 'Bob')
    balances = calculate_balances([alice, bob], [])
    assert balances[1] == Decimal('0')
    assert balances[2] == Decimal('0')


# --- Settlement tests ---

def test_settlement_simple():
    balances = {1: Decimal('50.00'), 2: Decimal('-50.00')}
    names = {1: 'Alice', 2: 'Bob'}
    result = calculate_settlements(balances, names)
    assert len(result) == 1
    assert result[0] == {'from_name': 'Bob', 'to_name': 'Alice', 'amount': Decimal('50.00')}


def test_settlement_three_members():
    balances = {1: Decimal('60.00'), 2: Decimal('-10.00'), 3: Decimal('-50.00')}
    names = {1: 'Alice', 2: 'Bob', 3: 'Carol'}
    result = calculate_settlements(balances, names)
    total_transferred = sum(t['amount'] for t in result)
    assert total_transferred == Decimal('60.00')
    assert len(result) <= 2  # at most N-1 transfers


def test_settlement_already_balanced():
    balances = {1: Decimal('0.00'), 2: Decimal('0.00')}
    names = {1: 'Alice', 2: 'Bob'}
    result = calculate_settlements(balances, names)
    assert result == []


def test_settlement_total_transfers_equal_total_credit():
    balances = {1: Decimal('100.00'), 2: Decimal('-30.00'), 3: Decimal('-70.00')}
    names = {1: 'Alice', 2: 'Bob', 3: 'Carol'}
    result = calculate_settlements(balances, names)
    assert sum(t['amount'] for t in result) == Decimal('100.00')


def test_settlement_amounts_are_positive():
    balances = {1: Decimal('25.00'), 2: Decimal('-25.00')}
    names = {1: 'Alice', 2: 'Bob'}
    result = calculate_settlements(balances, names)
    assert all(t['amount'] > 0 for t in result)
