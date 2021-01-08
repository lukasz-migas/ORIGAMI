# Standard library imports
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.handlers.load import LOAD_HANDLER
from origami.handlers.load import LoadHandler
from origami.objects.document import DocumentStore
from origami.objects.document import DocumentGroups

# enable on windowsOS only
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject

if sys.platform == "win32":

    from origami.readers.io_thermo_raw import ThermoRawReader
    from origami.readers.io_waters_raw import WatersIMReader
    from origami.readers.io_waters_raw_api import WatersRawReader


@pytest.fixture
def load_handler():
    """Initialize"""
    return LoadHandler()


class TestLoadHandler:
    def test_init(self):
        _load_handler = LoadHandler()
        assert _load_handler

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("dt_start, dt_end", ([0, 50], [20, 150], [150, 20]))
    @pytest.mark.parametrize("rt_start, rt_end", ([0, 2], [2, 5], [5, 2]))
    def test_waters_im_extract_ms(self, get_waters_im_small, dt_start, dt_end, rt_start, rt_end):
        obj = LOAD_HANDLER.waters_im_extract_ms(
            get_waters_im_small, dt_start=dt_start, dt_end=dt_end, rt_start=rt_start, rt_end=rt_end
        )

        assert isinstance(obj, MassSpectrumObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("dt_start, dt_end", ([0, 50], [20, 150], [150, 20]))
    @pytest.mark.parametrize("mz_start, mz_end", ([500, 750], [1550, 1250]))
    def test_waters_im_extract_rt(self, get_waters_im_small, dt_start, dt_end, mz_start, mz_end):
        obj = LOAD_HANDLER.waters_im_extract_rt(
            get_waters_im_small, dt_start=dt_start, dt_end=dt_end, mz_start=mz_start, mz_end=mz_end
        )

        assert isinstance(obj, ChromatogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("rt_start, rt_end", ([0, 2], [2, 5], [5, 2]))
    @pytest.mark.parametrize("mz_start, mz_end", ([500, 750], [1550, 1250]))
    def test_waters_im_extract_dt(self, get_waters_im_small, rt_start, rt_end, mz_start, mz_end):
        obj = LOAD_HANDLER.waters_im_extract_dt(
            get_waters_im_small, rt_start=rt_start, rt_end=rt_end, mz_start=mz_start, mz_end=mz_end
        )

        assert isinstance(obj, MobilogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("rt_start, rt_end", ([0, 2], [2, 5], [5, 2]))
    @pytest.mark.parametrize("mz_start, mz_end", ([500, 750], [1550, 1250]))
    @pytest.mark.parametrize("dt_start, dt_end", ([0, 200], [50, 150]))
    def test_waters_im_extract_heatmap(self, get_waters_im_small, rt_start, rt_end, mz_start, mz_end, dt_start, dt_end):
        obj = LOAD_HANDLER.waters_im_extract_heatmap(
            get_waters_im_small,
            rt_start=rt_start,
            rt_end=rt_end,
            mz_start=mz_start,
            mz_end=mz_end,
            dt_start=dt_start,
            dt_end=dt_end,
        )

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

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("mz_min, mz_max, mz_bin_size", ([500, 1000, 1.0], [500, 1000, 0.1]))
    def test_waters_im_extract_msdt(self, get_waters_im_small, mz_min, mz_max, mz_bin_size):
        obj = LOAD_HANDLER.waters_im_extract_msdt(get_waters_im_small, mz_min, mz_max, mz_bin_size)

        assert isinstance(obj, MassSpectrumHeatmapObject)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert obj.x.shape[0] == obj.array.shape[1]
        assert obj.y.shape[0] == obj.array.shape[0]
        assert np.diff(obj.x).mean() - mz_bin_size < 0.01

    def test_load_text_spectrum_data(self, get_text_ms_paths):
        for path in get_text_ms_paths:
            x, y, directory, x_limits, extension = LOAD_HANDLER.load_text_spectrum_data(path)
            assert isinstance(x, np.ndarray)
            assert isinstance(y, np.ndarray)
            assert len(x) == len(y)
            assert isinstance(x_limits, (list, tuple)) and len(x_limits) == 2
            assert isinstance(directory, str)
            assert isinstance(extension, str) and extension.startswith(".")

    def test_load_text_spectrum_document(self, get_text_ms_paths):
        for path in get_text_ms_paths:
            document = LOAD_HANDLER.load_text_mass_spectrum_document(path)
            assert isinstance(document, DocumentStore)

            mz = document[DocumentGroups.MassSpectrum, True]
            assert isinstance(mz, MassSpectrumObject)
            assert len(mz.x) == len(mz.y)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_thermo_ms_data(self, get_thermo_ms_small):
        reader, data = LOAD_HANDLER.load_thermo_ms_data(get_thermo_ms_small)
        assert isinstance(data, dict)
        assert isinstance(reader, ThermoRawReader)
        assert "mz" in data
        assert "rt" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_thermo_ms_document(self, get_thermo_ms_small):
        document = LOAD_HANDLER.load_thermo_ms_document(get_thermo_ms_small)
        assert isinstance(document, DocumentStore)

        rt = document["Chromatograms/Summed Chromatogram", True]
        assert isinstance(rt, ChromatogramObject)
        assert len(rt.x) == len(rt.y)

        mz = document["MassSpectra/Summed Spectrum", True]
        assert isinstance(mz, MassSpectrumObject)
        assert len(mz.x) == len(mz.y)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_ms_data(self, get_waters_im_small):
        reader, data = LOAD_HANDLER.load_waters_ms_data(get_waters_im_small)
        assert isinstance(data, dict)
        assert isinstance(reader, WatersRawReader)
        assert "mz" in data
        assert "rt" in data
        assert "dt" not in data
        assert "parameters" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_ms_document(self, get_waters_im_small):
        document = LOAD_HANDLER.load_waters_ms_document(get_waters_im_small)
        assert isinstance(document, DocumentStore)

        rt = document[DocumentGroups.Chromatogram, True]
        assert isinstance(rt, ChromatogramObject)
        assert len(rt.x) == len(rt.y)

        mz = document[DocumentGroups.MassSpectrum, True]
        assert isinstance(mz, MassSpectrumObject)
        assert len(mz.x) == len(mz.y)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_data(self, get_waters_im_small):
        reader, data = LOAD_HANDLER.load_waters_im_data(get_waters_im_small)
        assert isinstance(data, dict)
        assert isinstance(reader, WatersIMReader)
        assert "mz" in data and isinstance(data["mz"], MassSpectrumObject)
        assert "rt" in data and isinstance(data["rt"], ChromatogramObject)
        assert "dt" in data and isinstance(data["dt"], MobilogramObject)
        assert "heatmap" in data and isinstance(data["heatmap"], IonHeatmapObject)
        assert "msdt" in data and isinstance(data["msdt"], MassSpectrumHeatmapObject)
        assert "parameters" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_document(self, get_waters_im_small):
        document = LOAD_HANDLER.load_waters_im_document(get_waters_im_small)
        assert isinstance(document, DocumentStore)

        rt = document["Chromatograms/Summed Chromatogram", True]
        assert isinstance(rt, ChromatogramObject)
        assert len(rt.x) == len(rt.y)

        dt = document["Mobilograms/Summed Mobilogram", True]
        assert isinstance(dt, MobilogramObject)
        assert len(dt.x) == len(dt.y)

        mz = document["MassSpectra/Summed Spectrum", True]
        assert isinstance(mz, MassSpectrumObject)
        assert len(mz.x) == len(mz.y)
