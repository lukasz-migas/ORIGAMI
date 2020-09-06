"""Test secret"""
# Third-party imports
import pytest

# Local imports
from origami.utils.random import get_random_int
from origami.utils.random import random_int_0_to_255


@pytest.mark.parametrize("min_value, max_value", ([0, 255], [0, 651213], [12433, 3123145]))
def test_get_random_int(min_value, max_value):
    value = get_random_int(min_value, max_value)
    assert isinstance(value, int)
    assert min_value <= value <= max_value


def test_random_int_0_to_255():
    value = random_int_0_to_255()
    assert isinstance(value, int)
    assert 0 <= value <= 255
