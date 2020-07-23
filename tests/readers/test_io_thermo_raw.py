"""Test origami.readers.io_waters_raw.py"""
# Standard library imports
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.readers.config import DEFAULT_THERMO_FILTER
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    pytest.skip("skipping Linux-only tests", allow_module_level=True)


class TestThermoRawReader:
    def test_init(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        assert reader
        assert reader.mz_min < reader.mz_max
        assert len(reader.rt_bin) == reader.n_scans()
        assert len(reader.rt_min) == reader.n_scans()
        assert len(reader.scan_range) == 2
        assert len(reader.time_range) == 2
        assert len(reader.mass_range) == 2
        assert reader.n_filters() == len(reader._unique_filters)
        assert "m/z range" in str(reader)

    def test__getitem__(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        item_list = [0, 1]
        item_list.extend(reader._unique_filters)
        for item in item_list:
            obj = reader[item]
            assert isinstance(obj, MassSpectrumObject)
            assert len(obj.x) == len(obj.y)
            assert isinstance(obj.x, np.ndarray)
            assert isinstance(obj.y, np.ndarray)

        with pytest.raises(IndexError):
            _ = reader[3]

    def test_get_filter_by_idx(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        for i in range(reader.n_filters()):
            title = reader.get_filter_by_idx(i)
            assert isinstance(title, str)
            assert title != DEFAULT_THERMO_FILTER

        with pytest.raises(IndexError):
            _ = reader.get_filter_by_idx(3)

    def test_get_scan_info(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        scan_info = reader.get_scan_info()
        assert isinstance(scan_info, dict)
        assert len(scan_info) == reader.n_scans()

    def test_get_spectrum_for_each_filter(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        data = reader.get_spectrum_for_each_filter()
        assert isinstance(data, dict)
        assert len(data) == reader.n_filters()
        for title in reader._unique_filters:
            assert title in data

    def test_get_chromatogram_for_each_filter(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        data = reader.get_chromatogram_for_each_filter()
        assert isinstance(data, dict)
        assert len(data) == reader.n_filters()
        for title in reader._unique_filters:
            assert title in data

    @pytest.mark.parametrize("centroid", (True, False))
    def test__get_spectrum(self, get_thermo_ms_small, centroid):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        x, y = reader._get_spectrum(1, centroid)
        assert isinstance(x, np.ndarray)
        assert len(x) > 0
        assert len(x) == len(y)

        with pytest.raises(ValueError):
            reader._get_spectrum(0, centroid)

        with pytest.raises(ValueError):
            reader._get_spectrum(reader.n_scans() + 1, centroid)

    @pytest.mark.parametrize("start_scan", (-1, 5))
    @pytest.mark.parametrize("end_scan", (-1, 10))
    @pytest.mark.parametrize("centroid", (True, False))
    def test_get_spectrum(self, get_thermo_ms_small, start_scan, end_scan, centroid):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        obj = reader.get_spectrum(start_scan, end_scan, centroid=centroid)

        assert isinstance(obj, MassSpectrumObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    def test_get_tic(self, get_thermo_ms_small):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        obj = reader.get_tic()

        assert isinstance(obj, ChromatogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.parametrize("mz_start, mz_end", ([-1, -1], [500, 600], [-1, 1000], [500, -1]))
    @pytest.mark.parametrize("rt_start, rt_end", ([-1, -1], [-1, 1.0], [1.0, -1]))
    def test_get_chromatogram(self, get_thermo_ms_small, mz_start, mz_end, rt_start, rt_end):
        from origami.readers.io_thermo_raw import ThermoRawReader

        reader = ThermoRawReader(get_thermo_ms_small)
        obj = reader.get_chromatogram(mz_start, mz_end, rt_start, rt_end)

        assert isinstance(obj, ChromatogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
