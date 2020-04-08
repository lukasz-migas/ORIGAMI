"""Test origami.readers.io_waters_raw.py"""
# Standard library imports
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.readers.io_waters_raw_api import WatersRawReader

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    pytest.skip("skipping Linux-only tests", allow_module_level=True)


class TestWatersRawReader:
    @staticmethod
    def test_init(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)

        assert reader
        assert reader.mz_min < reader.mz_max
        assert len(reader.dt_bin) == reader.n_scans(1)
        assert len(reader.dt_ms) == reader.n_scans(1)
        assert len(reader.rt_bin) == reader.n_scans(0)
        assert len(reader.rt_min) == reader.n_scans(0)

    @staticmethod
    def test_check_fcn(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)
        with pytest.raises(ValueError):
            reader.check_fcn(reader.n_functions + 1)

    @staticmethod
    def test_get_tic(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_tic()
        assert len(x) == len(y)

    @staticmethod
    def test_get_bpi(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_bpi()
        assert len(x) == len(y)

    @staticmethod
    @pytest.mark.parametrize("mz_value, count", ([500, 1], [[500, 600], 2], [(500, 600), 2]))
    @pytest.mark.parametrize("tolerance", (0.1, 0.5))
    def test_get_chromatogram(get_waters_im_small, mz_value, count, tolerance):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_chromatogram(mz_value, tolerance)
        assert len(y) == count
        assert len(x) == reader.n_scans(0)

    @staticmethod
    @pytest.mark.parametrize("tolerance", (None, -1, 0))
    def test_get_chromatogram_wrong_tolerance(get_waters_im_small, tolerance):
        reader = WatersRawReader(get_waters_im_small)
        with pytest.raises(ValueError):
            reader.get_chromatogram(500, tolerance)

    @staticmethod
    @pytest.mark.parametrize("mz_value, count", ([500, 1], [[500, 600], 2], [(500, 600), 2]))
    @pytest.mark.parametrize("tolerance", (0.1, 0.5))
    def test_get_mobilogram(get_waters_im_small, mz_value, count, tolerance):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_mobilogram(mz_value, tolerance)
        assert len(y) == count
        assert len(x) == reader.n_scans(1)

    @staticmethod
    @pytest.mark.parametrize("tolerance", (None, -1, 0))
    def test_get_mobilogram_wrong_tolerance(get_waters_im_small, tolerance):
        reader = WatersRawReader(get_waters_im_small)
        with pytest.raises(ValueError):
            reader.get_mobilogram(500, tolerance)

    @staticmethod
    @pytest.mark.parametrize("start_scan", (None, 0, 500))
    @pytest.mark.parametrize("end_scan", (None, 10))
    def test_get_spectrum(get_waters_im_small, start_scan, end_scan):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_spectrum(start_scan, end_scan)
        assert len(x) == len(y)
        assert y.dtype == np.float32

    @staticmethod
    def test__get_spectrum(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader._get_spectrum(0, 1)
        assert len(x) == len(y)

    @staticmethod
    def test_get_average_spectrum(get_waters_im_small):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_average_spectrum(0)
        assert len(x) == len(y)

    @staticmethod
    @pytest.mark.parametrize("start_scan", (None, 0, 500))
    @pytest.mark.parametrize("end_scan", (None, 10))
    @pytest.mark.parametrize("start_drift", (None, 0))
    @pytest.mark.parametrize("end_drift", (None, 100))
    def test_get_drift_spectrum(get_waters_im_small, start_scan, end_scan, start_drift, end_drift):
        reader = WatersRawReader(get_waters_im_small)
        x, y = reader.get_drift_spectrum(start_scan, end_scan, start_drift=start_drift, end_drift=end_drift)
        assert len(x) == len(y)
        assert y.dtype == np.float32
