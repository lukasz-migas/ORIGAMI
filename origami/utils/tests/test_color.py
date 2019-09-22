"""Test utils.color.py"""
from utils.color import convert_rgb_1_to_255
from utils.color import convert_rgb_255_to_1
from utils.color import get_font_color


class TestColor(object):
    @staticmethod
    def test_convertRGB1to255():
        # check float
        expected_value = [255.0, 255.0, 255.0]
        return_value = convert_rgb_1_to_255([1.0, 1.0, 1.0], decimals=1, as_integer=False)

        assert expected_value == return_value

        # check integer
        expected_value = [255, 255, 255]
        return_value = convert_rgb_1_to_255([1.0, 1.0, 1.0], decimals=1, as_integer=True)

        assert expected_value == return_value

    @staticmethod
    def test_convertRGB255to1():
        expected_value = [1.0, 1.0, 1.0]
        return_value = convert_rgb_255_to_1([255.0, 255.0, 255.0], decimals=1)

        assert expected_value == return_value

    @staticmethod
    def test_determineFontColor():
        expected_value = (255, 255, 255)  # white
        return_value = get_font_color([0.0, 0.0, 0.0], return_rgb=True)

        assert expected_value == return_value

        # check font color and return string
        expected_value = (255, 255, 255)  # white
        return_value = get_font_color([0.0, 0.0, 0.0], return_rgb=True, convert1to255=True)

        assert expected_value == return_value

        # check font color and return white
        expected_value = "white"  # white
        return_value = get_font_color([0.0, 0.0, 0.0], return_rgb=False)

        assert expected_value == return_value

        # check font color and return black
        expected_value = "black"  # black
        return_value = get_font_color([255, 255, 255], return_rgb=False)

        assert expected_value == return_value
