from decimal import Decimal
import pytest
from pots.splits import calculate_splits


def test_equal_split_two_members():
    result = calculate_splits(Decimal('100.00'), {1: 1, 2: 1})
    assert result[1] + result[2] == Decimal('100.00')
    assert result[1] == Decimal('50.00')
    assert result[2] == Decimal('50.00')


def test_equal_split_three_members():
    result = calculate_splits(Decimal('100.00'), {1: 1, 2: 1, 3: 1})
    assert result[1] + result[2] + result[3] == Decimal('100.00')
    # Two members get 33.33, last gets 33.34 (remainder)
    assert result[1] == Decimal('33.33')
    assert result[2] == Decimal('33.33')
    assert result[3] == Decimal('33.34')


def test_weighted_split():
    result = calculate_splits(Decimal('100.00'), {1: 2, 2: 1})
    assert result[1] + result[2] == Decimal('100.00')
    assert result[1] == Decimal('66.66')
    assert result[2] == Decimal('33.34')


def test_zero_weight_excluded():
    result = calculate_splits(Decimal('90.00'), {1: 1, 2: 1, 3: 0})
    assert 3 not in result
    assert result[1] + result[2] == Decimal('90.00')


def test_subset_of_members():
    result = calculate_splits(Decimal('60.00'), {1: 1, 2: 2})
    assert result[1] + result[2] == Decimal('60.00')
    assert result[1] == Decimal('20.00')
    assert result[2] == Decimal('40.00')


def test_single_member_gets_full_amount():
    result = calculate_splits(Decimal('42.50'), {1: 5})
    assert result[1] == Decimal('42.50')


def test_all_zero_weights_raises():
    with pytest.raises(ValueError):
        calculate_splits(Decimal('100.00'), {1: 0, 2: 0})


def test_empty_weights_raises():
    with pytest.raises(ValueError):
        calculate_splits(Decimal('100.00'), {})


def test_total_always_exact():
    # Tricky amount that would accumulate rounding errors
    result = calculate_splits(Decimal('10.00'), {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1})
    assert sum(result.values()) == Decimal('10.00')
