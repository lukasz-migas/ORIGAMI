"""Test check functions"""
from utils.check import check_value_order
from utils.check import isbool


def test_check_value_order_bad_order():
    expected_value_min, expected_value_max = 24, 42
    return_value_min, return_value_max = check_value_order(42, 24)

    assert expected_value_min == return_value_min and expected_value_max == return_value_max


def test_check_value_order_good_order():
    expected_value_min, expected_value_max = 24, 42
    return_value_min, return_value_max = check_value_order(24, 42)

    assert expected_value_min == return_value_min and expected_value_max == return_value_max


def test_isbool_good():
    expected = True
    returned = isbool(True)

    assert expected == returned


def test_isbool_bad():
    expected = False
    returned = isbool('True')

    assert expected == returned
