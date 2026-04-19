from decimal import Decimal
import pytest
from pots.bot_parser import parse_drop_command, resolve_member_specs


# --- parse_drop_command ---

def test_simple_drop():
    r = parse_drop_command('120 team dinner')
    assert r['amount'] == Decimal('120')
    assert r['tokens'] == ['team', 'dinner']


def test_drop_with_decimal_amount():
    r = parse_drop_command('45.50 taxi home')
    assert r['amount'] == Decimal('45.50')


def test_drop_quoted_description():
    r = parse_drop_command('120 "team dinner after work"')
    assert r['tokens'] == ['team dinner after work']


def test_section_marker_without_leading_space():
    # "41/paid" should be split into "41" and "/paid"
    r = parse_drop_command('41 test 41/paid @rgezikov')
    assert r['tokens'] == ['test', '41', '/paid', '@rgezikov']


def test_missing_description_raises():
    with pytest.raises(ValueError, match='Description'):
        parse_drop_command('120')


def test_invalid_amount_raises():
    with pytest.raises(ValueError, match='Invalid amount'):
        parse_drop_command('abc dinner')


def test_zero_amount_raises():
    with pytest.raises(ValueError, match='positive'):
        parse_drop_command('0 dinner')


def test_negative_amount_raises():
    with pytest.raises(ValueError, match='positive'):
        parse_drop_command('-10 dinner')


def test_empty_input_raises():
    with pytest.raises(ValueError):
        parse_drop_command('')


# --- resolve_member_specs ---

class FakeMember:
    def __init__(self, id, name, username=''):
        self.id = id
        self.name = name
        self.telegram_username = username


def test_no_sections_equal_split():
    members = [FakeMember(1, 'Alice', 'alice'), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['team', 'dinner'], members)
    assert desc == 'team dinner'
    assert weights is None
    assert payer is None


def test_paid_section_by_username():
    members = [FakeMember(1, 'Alice', 'alice'), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['dinner', '/paid', '@alice'], members)
    assert desc == 'dinner'
    assert payer is not None and payer.id == 1


def test_paid_section_username_case_insensitive():
    members = [FakeMember(1, 'Alice', 'alice')]
    desc, weights, payer = resolve_member_specs(['dinner', '/paid', '@Alice'], members)
    assert payer is not None and payer.id == 1


def test_paid_name_without_at_not_matched():
    # Name-based lookup no longer supported — 'Alice Smith' is not a username
    members = [FakeMember(1, 'Alice Smith', 'asmith')]
    desc, weights, payer = resolve_member_specs(['dinner', '/paid', 'Alice', 'Smith'], members)
    assert payer is None


def test_split_section_by_username():
    members = [FakeMember(1, 'Alice', 'alice'), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['dinner', '/split', '@alice:1,', '@bob:2'], members)
    assert desc == 'dinner'
    assert weights == {1: Decimal('1'), 2: Decimal('2')}


def test_paid_and_split_sections():
    members = [FakeMember(1, 'Roman', 'roman'), FakeMember(2, 'Roman G', 'rgezikov')]
    desc, weights, payer = resolve_member_specs(
        ['payback', '/paid', '@roman', '/split', '@roman:1,', '@rgezikov:2'],
        members,
    )
    assert desc == 'payback'
    assert payer is not None and payer.id == 1
    assert weights == {1: Decimal('1'), 2: Decimal('2')}


def test_split_unknown_username_skipped():
    members = [FakeMember(1, 'Alice', 'alice')]
    desc, weights, payer = resolve_member_specs(['dinner', '/split', '@alice:1,', '@nobody:2'], members)
    assert weights == {1: Decimal('1')}


def test_legacy_at_payer_at_end_of_description():
    members = [FakeMember(1, 'Alice', 'alice')]
    desc, weights, payer = resolve_member_specs(['dinner', '@alice'], members)
    assert desc == 'dinner'
    assert payer is not None and payer.id == 1


def test_split_single_member_no_weight():
    members = [FakeMember(1, 'Alice', 'alice'), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['settlement', '/split', '@alice'], members)
    assert weights == {1: Decimal('1')}


def test_split_multiple_members_no_weight():
    members = [FakeMember(1, 'Alice', 'alice'), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['dinner', '/split', '@alice,', '@bob'], members)
    assert weights == {1: Decimal('1'), 2: Decimal('1')}


def test_space_before_colon_in_split():
    # Telegram picker inserts @username followed by a space, user then types :weight
    # Result: "@RGezikovRus :5, @RGezikov :3" — space between username and colon
    members = [FakeMember(1, 'Roman G', 'rgezikovrus'), FakeMember(2, 'Roman', 'rgezikov')]
    r = parse_drop_command('42 test 42 /paid @RGezikovRus /split @RGezikovRus :5, @RGezikov :3')
    desc, weights, payer = resolve_member_specs(r['tokens'], members)
    assert desc == 'test 42'
    assert payer is not None and payer.id == 1
    assert weights == {1: Decimal('5'), 2: Decimal('3')}


def test_member_without_username_not_matchable():
    members = [FakeMember(1, 'Alice', ''), FakeMember(2, 'Bob', 'bob')]
    desc, weights, payer = resolve_member_specs(['dinner', '/split', '@alice:1,', '@bob:2'], members)
    # Alice has no username — not matchable
    assert 1 not in (weights or {})
    assert weights == {2: Decimal('2')}
