"""Test origami.readers.io_waters_raw.py"""
# Standard library imports
import os
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.readers.io_waters_raw import WatersIMReader

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    pytest.skip("skipping Linux-only tests", allow_module_level=True)


class TestWatersIMReader:
    @staticmethod
    def test_init(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)

        assert reader
        assert reader._last is None
        assert reader.mz_min < reader.mz_max
        assert reader._driftscope is not None
        assert len(reader.dt_bin) == 200
        assert len(reader.dt_ms) == 200
        assert len(reader.rt_bin) == reader.n_scans(0)
        assert len(reader.rt_min) == reader.n_scans(0)

    @staticmethod
    def test_get_ms(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, y = reader.extract_ms()
        assert len(x) == len(y)

    @staticmethod
    def test_extract_ms(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_ms(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    def test_get_dt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, y = reader.extract_dt()
        assert len(x) == len(y)
        assert x.dtype == np.int32

    @staticmethod
    def test_extract_dt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_dt(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    def test_get_rt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        x, x_bin, y = reader.extract_rt()
        assert len(x) == len(x_bin) == len(y)
        assert x_bin.dtype == np.int32

    @staticmethod
    def test_extract_rt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_rt(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    @pytest.mark.parametrize("reduce", ("sum", "mean", "median"))
    def test_get_heatmap(get_waters_im_small, reduce):
        reader = WatersIMReader(get_waters_im_small)
        dt_x, dt_y, rt_x, rt_y, heatmap = reader.extract_heatmap(reduce=reduce)

        assert heatmap.shape[0] == 200 == len(dt_x) == len(dt_y)
        assert heatmap.shape[1] == reader.n_scans(0) == len(rt_x) == len(rt_y)

    @staticmethod
    def test_extract_heatmap(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    @pytest.mark.parametrize("n_points", (100, 1000, 5000))
    def test_get_msdt(get_waters_im_small, n_points):
        reader = WatersIMReader(get_waters_im_small)
        mz_x, mz_y, dt_x, dt_y, heatmap = reader.extract_msdt(n_points=n_points)

        assert heatmap.shape[0] == 200 == len(dt_x) == len(dt_y)
        assert heatmap.shape[1] == n_points == len(mz_x) == len(mz_y)

    @staticmethod
    def test_extract_msdt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)
