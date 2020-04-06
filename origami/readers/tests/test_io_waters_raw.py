"""Test origami.readers.io_waters_raw.py"""
# Standard library imports
import os
import sys

# Third-party imports
import numpy as np
import pytest
from numpy.testing import assert_array_equal

# Local imports
from origami.readers.io_waters_raw import WatersIMReader

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    pytest.skip("skipping Linux-only tests", allow_module_level=True)


class TestWatersIMReader:
    def test_init(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)

        assert reader
        assert reader._last is None
        assert reader.mz_min < reader.mz_max
        assert reader._driftscope is not None
        assert len(reader.dt_bin) == 200
        assert len(reader.dt_ms) == 200
        assert len(reader.rt_bin) == reader.n_scans
        assert len(reader.rt_min) == reader.n_scans

    def test_get_ms(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, y, y_norm = reader.extract_ms(normalize=False)
        assert len(x) == len(y) == len(y_norm)
        assert_array_equal(y, y_norm)

        x, y, y_norm = reader.extract_ms(normalize=True)
        assert y_norm.max() <= 1.0

    def test_extract_ms(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_ms(return_data=False)
        assert os.path.exists(path)

    def test_get_dt(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, y, y_norm = reader.extract_dt(normalize=False)
        assert len(x) == len(y) == len(y_norm)
        assert_array_equal(y, y_norm)
        assert x.dtype == np.int32

        x, y, y_norm = reader.extract_dt(normalize=True)
        assert y_norm.max() <= 1.0

    def test_extract_dt(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_dt(return_data=False)
        assert os.path.exists(path)

    def test_get_rt(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, x_bin, y, y_norm = reader.extract_rt(normalize=False)
        assert len(x) == len(x_bin) == len(y) == len(y_norm)
        assert_array_equal(y, y_norm)
        assert x_bin.dtype == np.int32

        x, x_bin, y, y_norm = reader.extract_rt(normalize=True)
        assert y_norm.max() <= 1.0

    def test_extract_rt(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_rt(return_data=False)
        assert os.path.exists(path)

    @pytest.mark.parametrize("reduce", ("sum", "mean", "median"))
    def test_get_heatmap(self, get_waters_im_small, reduce):
        reader = WatersIMReader(get_waters_im_small)
        heatmap, heatmap_norm = reader.extract_heatmap(normalize=False, reduce=reduce)

        assert_array_equal(heatmap, heatmap_norm)
        assert heatmap.shape[0] == 200
        assert heatmap.shape[1] == reader.n_scans

    def test_extract_heatmap(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)

    @pytest.mark.parametrize("n_points", (100, 1000, 5000))
    def test_get_msdt(self, get_waters_im_small, n_points):
        reader = WatersIMReader(get_waters_im_small)
        heatmap, heatmap_norm = reader.extract_msdt(n_points=n_points, normalize=False)

        assert_array_equal(heatmap, heatmap_norm)
        assert heatmap.shape[0] == 200
        assert heatmap.shape[1] == n_points

    def test_extract_msdt(self, get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)
