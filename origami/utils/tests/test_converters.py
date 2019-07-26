"""Test converters in utils.converters.py"""
from utils.converters import byte2str
from utils.converters import float2int
from utils.converters import num2str
from utils.converters import str2bool
from utils.converters import str2int
from utils.converters import str2num


class TestConverters(object):
    @staticmethod
    def test_byte2str():
        expected_value = "42.0"
        return_value = byte2str(b"42.0")

        assert expected_value == return_value

        expected_value = "42.0"
        return_value = byte2str(42.0)

        assert expected_value != return_value

    @staticmethod
    def test_str2num():
        expected_value = 42.0
        return_value = str2num("42")

        assert expected_value == return_value

        expected_value = 42.0
        return_value = str2num("FAIL")

        assert expected_value != return_value

    @staticmethod
    def test_num2str():
        expected_value = "42.0"
        return_value = num2str(42.0)

        assert expected_value == return_value

        expected_value = "42.0"
        return_value = num2str("FAIL")

        assert expected_value != return_value

    @staticmethod
    def test_str2int():
        expected_value = 42
        return_value = str2int("42")

        assert expected_value == return_value

        expected_value = 42
        return_value = str2int("FAIL")

        assert expected_value != return_value

    @staticmethod
    def test_float2int():
        expected_value = 42
        return_value = float2int(42.0)

        assert expected_value == return_value

        expected_value = 42
        return_value = float2int("FAIL")

        assert expected_value != return_value

    @staticmethod
    def test_str2bool():
        expected_value = True
        return_value = str2bool("True")

        assert expected_value == return_value

        expected_value = True
        return_value = str2bool(True)

        assert expected_value != return_value
