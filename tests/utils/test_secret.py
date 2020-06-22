"""Test secret"""
# Local imports
from origami.utils.secret import get_short_hash


def test_get_short_hash():
    value = get_short_hash()
    assert isinstance(value, str)
