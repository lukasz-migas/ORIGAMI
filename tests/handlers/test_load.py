# Standard library imports
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.handlers.load import LoadHandler
from origami.objects.document import DocumentStore

# enable on windowsOS only
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject

if sys.platform == "win32":
    from origami.readers.io_waters_raw import WatersIMReader
    from origami.readers.io_waters_raw_api import WatersRawReader
    from origami.readers.io_thermo_raw import ThermoRawReader


@pytest.fixture
def load_handler():
    return LoadHandler()


class TestLoadHandler:
    def test_init(self):
        _load_handler = LoadHandler()
        assert _load_handler

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_extract_ms_from_mobilogram(self, load_handler, get_waters_im_small):
        assert True

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_extract_ms_from_chromatogram(self, load_handler, get_waters_im_small):
        assert True

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_extract_heatmap_from_mass_spectrum_one(self, load_handler, get_waters_im_small):
        assert True

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_extract_heatmap_from_mass_spectrum_many(self, load_handler, get_waters_im_small):
        assert True

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_ms(self, load_handler, get_waters_im_small):
        obj = load_handler.waters_im_extract_ms(get_waters_im_small)

        assert isinstance(obj, MassSpectrumObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_rt(self, load_handler, get_waters_im_small):
        obj = load_handler.waters_im_extract_rt(get_waters_im_small)

        assert isinstance(obj, ChromatogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_dt(self, load_handler, get_waters_im_small):
        obj = load_handler.waters_im_extract_dt(get_waters_im_small)

        assert isinstance(obj, MobilogramObject)
        assert len(obj.x) == len(obj.y)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_heatmap(self, load_handler, get_waters_im_small):
        obj = load_handler.waters_im_extract_heatmap(get_waters_im_small)

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
    def test_waters_im_extract_msdt(self, load_handler, get_waters_im_small, mz_min, mz_max, mz_bin_size):
        obj = load_handler.waters_im_extract_msdt(get_waters_im_small, mz_min, mz_max, mz_bin_size)

        assert isinstance(obj, MassSpectrumHeatmapObject)
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert obj.x.shape[0] == obj.array.shape[1]
        assert obj.y.shape[0] == obj.array.shape[0]
        assert np.diff(obj.x).mean() - mz_bin_size < 0.01

    def test_load_text_mass_spectrum_data(self):
        assert True

    def test_load_text_annotated_data(self):
        assert True

    def test_load_text_heatmap_data(self):
        assert True

    def test_load_mgf_data(self):
        assert True

    def test_load_mgf_document(self):
        assert True

    def test_load_mzml_data(self):
        assert True

    def test_load_mzml_document(self):
        assert True

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_thermo_ms_data(self, load_handler, get_thermo_ms_small):
        reader, data = load_handler.load_thermo_ms_data(get_thermo_ms_small)
        assert isinstance(data, dict)
        assert isinstance(reader, ThermoRawReader)
        assert "mz" in data
        assert "rt" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_thermo_ms_document(self, load_handler, get_thermo_ms_small):
        document = load_handler.load_thermo_ms_document(get_thermo_ms_small)
        assert isinstance(document, DocumentStore)

        rt = document["Chromatograms/Summed Chromatogram", True]
        assert isinstance(rt, ChromatogramObject)
        assert len(rt.x) == len(rt.y)

        mz = document["MassSpectra/Summed Spectrum", True]
        assert isinstance(mz, MassSpectrumObject)
        assert len(mz.x) == len(mz.y)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_ms_data(self, load_handler, get_waters_im_small):
        reader, data = load_handler.load_waters_ms_data(get_waters_im_small)
        assert isinstance(data, dict)
        assert isinstance(reader, WatersRawReader)
        assert "mz" in data
        assert "rt" in data
        assert "dt" not in data
        assert "parameters" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_ms_document(self, load_handler, get_waters_im_small):
        document = load_handler.load_waters_ms_document(get_waters_im_small)
        assert isinstance(document, DocumentStore)

        rt = document["Chromatograms/Summed Chromatogram", True]
        assert isinstance(rt, ChromatogramObject)
        assert len(rt.x) == len(rt.y)

        mz = document["MassSpectra/Summed Spectrum", True]
        assert isinstance(mz, MassSpectrumObject)
        assert len(mz.x) == len(mz.y)

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_data(self, load_handler, get_waters_im_small):
        reader, data = load_handler.load_waters_im_data(get_waters_im_small)
        assert isinstance(data, dict)
        assert isinstance(reader, WatersIMReader)
        assert "mz" in data and isinstance(data["mz"], MassSpectrumObject)
        assert "rt" in data and isinstance(data["rt"], ChromatogramObject)
        assert "dt" in data and isinstance(data["dt"], MobilogramObject)
        assert "heatmap" in data and isinstance(data["heatmap"], IonHeatmapObject)
        assert "msdt" in data and isinstance(data["msdt"], MassSpectrumHeatmapObject)
        assert "parameters" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_document(self, load_handler, get_waters_im_small):
        document = load_handler.load_waters_im_document(get_waters_im_small)
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
