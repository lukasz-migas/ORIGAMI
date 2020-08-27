"""Test containers"""
# Third-party imports
import numpy as np
from zarr import zeros

# Local imports
from origami.objects.container import ExtraDataStore


class TestExtraDataStore:
    def test_init(self):
        extra_data = ExtraDataStore()

        arr_1 = zeros((100, 100))
        arr_2 = zeros((100, 100))[:]
        extra_data.update({"arr_1": arr_1, "arr_2": arr_2})

        assert isinstance(extra_data["arr_1"], np.ndarray)
        assert isinstance(extra_data["arr_2"], np.ndarray)
