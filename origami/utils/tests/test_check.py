"""Test check functions"""
from utils.check import check_value_order
from utils.check import isbool
from utils.check import isnumber


class TestCheck(object):

    @staticmethod
    def test_check_value_order():
        # test bad order
        expected_value_min, expected_value_max = 24, 42
        return_value_min, return_value_max = check_value_order(42, 24)

        assert expected_value_min == return_value_min and expected_value_max == return_value_max

        # test good order
        expected_value_min, expected_value_max = 24, 42
        return_value_min, return_value_max = check_value_order(24, 42)

        assert expected_value_min == return_value_min and expected_value_max == return_value_max

        # test incorrect dtype
        expected_value_min, expected_value_max = '24', '42'
        return_value_min, return_value_max = check_value_order('24', '42')

        assert expected_value_min == return_value_min and expected_value_max == return_value_max

    @staticmethod
    def test_isbool():
        # test good bool
        expected = True
        returned = isbool(True)

        assert expected == returned

        # test bad bool
        expected = False
        returned = isbool('True')

        assert expected == returned

    @staticmethod
    def test_isnumber():
        # test good number
        expected = True
        returned = isnumber(42)

        assert expected == returned

        # test bad number
        expected = False
        returned = isnumber('42')

        assert expected == returned
