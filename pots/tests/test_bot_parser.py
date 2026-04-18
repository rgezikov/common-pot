from decimal import Decimal
import pytest
from pots.bot_parser import parse_drop_command


def test_simple_drop():
    r = parse_drop_command('120 team dinner')
    assert r['amount'] == Decimal('120')
    assert r['description'] == 'team dinner'
    assert r['payer_username'] is None


def test_drop_with_payer():
    r = parse_drop_command('120 team dinner @Bob')
    assert r['amount'] == Decimal('120')
    assert r['description'] == 'team dinner'
    assert r['payer_username'] == 'bob'


def test_drop_with_decimal_amount():
    r = parse_drop_command('45.50 taxi home @alice')
    assert r['amount'] == Decimal('45.50')
    assert r['description'] == 'taxi home'
    assert r['payer_username'] == 'alice'


def test_drop_quoted_double():
    r = parse_drop_command('120 "team dinner after work" @Bob')
    assert r['description'] == 'team dinner after work'
    assert r['payer_username'] == 'bob'


def test_drop_quoted_single():
    r = parse_drop_command("45.50 'taxi home' @Alice")
    assert r['description'] == 'taxi home'
    assert r['payer_username'] == 'alice'


def test_drop_no_payer_quoted():
    r = parse_drop_command('100 "team lunch"')
    assert r['description'] == 'team lunch'
    assert r['payer_username'] is None


def test_payer_username_lowercased():
    r = parse_drop_command('50 coffee @BOB')
    assert r['payer_username'] == 'bob'


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
