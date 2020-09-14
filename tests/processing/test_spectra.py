"""Test origami.processing.spectra"""
# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.processing.spectra import normalize_1d


@pytest.mark.parametrize("y", ([1, 2, 3, 4, 5], range(100), np.arange(100)))
def test_normalize_1d(y):
    _y = normalize_1d(y)
    assert len(y) == len(_y)
    assert isinstance(_y, np.ndarray)
    assert _y.max() == 1
