# Local imports
# Third-party imports
import numpy as np
import pytest

from origami.processing.utils import nthroot
from origami.processing.utils import find_nearest_index


def test_nthroot():
    expected = 3.0
    result = nthroot(9, 2)
    assert expected == result


@pytest.mark.parametrize("x, value, expected", ([[0, 1, 2, 3], 1, 1], [[0, 1, 2, 33, 55], [1, 50], [1, 4]]))
def test_find_nearest_index(x, value, expected):
    result = find_nearest_index(x, value)
    np.testing.assert_array_equal(result, expected)
