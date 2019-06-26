"""Test check functions"""
from utils.check import check_value_order


def test_check_value_order():
    expected_value_min, expected_value_max = 24, 42
    return_value_min, return_value_max = check_value_order(42, 24)

    assert expected_value_min == return_value_min and expected_value_max == return_value_max
