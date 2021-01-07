"""Test origami.readers.io_waters_raw.py"""
# Standard library imports
import os
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    pytest.skip("skipping Linux-only tests", allow_module_level=True)

if sys.platform == "win32":
    # Local imports
    from origami.readers.io_waters_raw import WatersIMReader


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
        assert os.path.exists(reader._driftscope)
        assert os.path.isfile(reader.driftscope_path)

    @staticmethod
    def test_get_ms(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        obj = reader.extract_ms()

        assert isinstance(obj, MassSpectrumObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @staticmethod
    def test_extract_ms(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_ms(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    def test_get_dt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        obj = reader.extract_dt()

        assert isinstance(obj, MobilogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @staticmethod
    def test_extract_dt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_dt(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    def test_get_rt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        obj = reader.extract_rt()

        assert isinstance(obj, ChromatogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @staticmethod
    def test_extract_rt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_rt(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    @pytest.mark.parametrize("reduce", ("sum", "mean", "median"))
    def test_get_heatmap(get_waters_im_small, reduce):
        reader = WatersIMReader(get_waters_im_small)
        obj = reader.extract_heatmap(reduce=reduce)

        assert isinstance(obj, IonHeatmapObject)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.xy, np.ndarray)
        assert isinstance(obj.yy, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert len(obj.x) == len(obj.xy)
        assert len(obj.y) == len(obj.yy)
        assert obj.x.shape[0] == obj.array.shape[1]
        assert obj.y.shape[0] == obj.array.shape[0]

    @staticmethod
    def test_extract_heatmap(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)

    @staticmethod
    @pytest.mark.parametrize("n_points", (100, 1000, 5000))
    def test_get_msdt(get_waters_im_small, n_points):
        reader = WatersIMReader(get_waters_im_small)
        obj = reader.extract_msdt(n_points=n_points)

        assert isinstance(obj, MassSpectrumHeatmapObject)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.xy, np.ndarray)
        assert isinstance(obj.yy, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert len(obj.x) == len(obj.xy)
        assert len(obj.y) == len(obj.yy)
        assert obj.x.shape[0] == obj.array.shape[1]
        assert obj.y.shape[0] == obj.array.shape[0]

    @staticmethod
    def test_extract_msdt(get_waters_im_small):
        reader = WatersIMReader(get_waters_im_small)
        path = reader.extract_heatmap(return_data=False)
        assert os.path.exists(path)
