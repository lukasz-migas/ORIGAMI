"""Test utils.color.py"""

from utils.color import convertRGB1to255, convertRGB255to1, determineFontColor


def test_convertRGB1to255():
    expected_value = [255., 255., 255.]
    return_value = convertRGB1to255([1., 1., 1.], decimals=1, as_integer=False)

    assert expected_value == return_value


def test_convertRGB1to255_as_integer():
    expected_value = [255, 255, 255]
    return_value = convertRGB1to255([1., 1., 1.], decimals=1, as_integer=True)

    assert expected_value == return_value


def test_convertRGB255to1():
    expected_value = [1., 1., 1.]
    return_value = convertRGB255to1([255., 255., 255.], decimals=1)

    assert expected_value == return_value


def test_determineFontColor_return_rgb():
    expected_value = (255, 255, 255)  # white
    return_value = determineFontColor([0., 0., 0.], return_rgb=True)

    assert expected_value == return_value


def test_determineFontColor_return_string_1to_255():
    expected_value = (255, 255, 255)  # white
    return_value = determineFontColor([0., 0., 0.], return_rgb=True, convert1to255=True)

    assert expected_value == return_value


def test_determineFontColor_return_string_white():
    expected_value = "white"  # white
    return_value = determineFontColor([0., 0., 0.], return_rgb=False)

    assert expected_value == return_value


def test_determineFontColor_return_string_black():
    expected_value = "black"  # black
    return_value = determineFontColor([255, 255, 255], return_rgb=False)

    assert expected_value == return_value
