"""Test converters in utils.converters.py"""

from utils.converters import str2num, num2str, str2int, float2int, str2bool, byte2str, check_value_order


def test_byte2str():
    expected_value = "42.0"
    return_value = byte2str(b"42.0")

    assert expected_value == return_value


def test_byte2str_fail():
    expected_value = "42.0"
    return_value = byte2str(42.0)

    assert expected_value != return_value


def test_str2num():
    expected_value = 42.0
    return_value = str2num("42")

    assert expected_value == return_value


def test_str2num_fail():
    expected_value = 42.0
    return_value = str2num("FAIL")

    assert expected_value != return_value


def test_num2str():
    expected_value = "42.0"
    return_value = num2str(42.0)

    assert expected_value == return_value


def test_num2str_fail():
    expected_value = "42.0"
    return_value = num2str("FAIL")

    assert expected_value != return_value


def test_str2int():
    expected_value = 42
    return_value = str2int("42")

    assert expected_value == return_value


def test_str2int_fail():
    expected_value = 42
    return_value = str2int("FAIL")

    assert expected_value != return_value


def test_float2int():
    expected_value = 42
    return_value = float2int(42.0)

    assert expected_value == return_value


def test_float2int_fail():
    expected_value = 42
    return_value = float2int("FAIL")

    assert expected_value != return_value


def test_str2bool():
    expected_value = True
    return_value = str2bool("True")

    assert expected_value == return_value


def test_str2bool_fail():
    expected_value = True
    return_value = str2bool(True)

    assert expected_value != return_value


def test_check_value_order():
    expected_value_min, expected_value_max = 24, 42
    return_value_min, return_value_max = check_value_order(42, 24)

    assert expected_value_min == return_value_min and expected_value_max == return_value_max
