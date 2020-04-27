# Standard library imports
import sys

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.document import document as Document
from origami.handlers.load import LoadHandler

# enable on windowsOS only
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
        x, y = load_handler.waters_im_extract_ms(get_waters_im_small)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(x) == len(y)
        assert np.max(y) >= 1  # check that values are correctly rescaled

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_rt(self, load_handler, get_waters_im_small):
        x, y = load_handler.waters_im_extract_rt(get_waters_im_small)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(x) == len(y)
        assert np.max(y) >= 1  # check that values are correctly rescaled

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_dt(self, load_handler, get_waters_im_small):
        x, y = load_handler.waters_im_extract_dt(get_waters_im_small)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(x) == len(y)
        assert np.max(y) >= 1  # check that values are correctly rescaled

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_waters_im_extract_heatmap(self, load_handler, get_waters_im_small):
        x, y, array = load_handler.waters_im_extract_heatmap(get_waters_im_small)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(array, np.ndarray)
        assert x.shape[0] == array.shape[0]
        assert y.shape[0] == array.shape[1]

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    @pytest.mark.parametrize("mz_min, mz_max, mz_bin_size", ([500, 1000, 1.0], [500, 1000, 0.1]))
    def test_waters_im_extract_msdt(self, load_handler, get_waters_im_small, mz_min, mz_max, mz_bin_size):
        x, y, array = load_handler.waters_im_extract_msdt(get_waters_im_small, mz_min, mz_max, mz_bin_size)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(array, np.ndarray)
        assert x.shape[0] == array.shape[0]
        assert y.shape[0] == array.shape[1]
        assert np.diff(x).mean() - mz_bin_size < 0.01
        assert x[0] <= mz_min
        assert x[-1] >= mz_max

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
        assert isinstance(document, Document)
        assert "xvals" in document.massSpectrum and "yvals" in document.massSpectrum
        assert len(document.massSpectrum["xvals"]) == len(document.massSpectrum["yvals"])
        assert "xvals" in document.RT and "yvals" in document.RT
        assert len(document.RT["xvals"]) == len(document.RT["yvals"])

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
        assert isinstance(document, Document)
        assert "xvals" in document.massSpectrum and "yvals" in document.massSpectrum
        assert len(document.massSpectrum["xvals"]) == len(document.massSpectrum["yvals"])
        assert "xvals" in document.RT and "yvals" in document.RT
        assert len(document.RT["xvals"]) == len(document.RT["yvals"])

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_data(self, load_handler, get_waters_im_small):
        reader, data = load_handler.load_waters_im_data(get_waters_im_small)
        assert isinstance(data, dict)
        assert isinstance(reader, WatersIMReader)
        assert "mz" in data
        assert "rt" in data
        assert "dt" in data
        assert "heatmap" in data
        assert "msdt" in data
        assert "parameters" in data

    @pytest.mark.skipif(sys.platform != "win32", reason="Cannot extract data on MacOSX or Linux")
    def test_load_waters_im_document(self, load_handler, get_waters_im_small):
        document = load_handler.load_waters_im_document(get_waters_im_small)
        assert isinstance(document, Document)
        assert "xvals" in document.massSpectrum and "yvals" in document.massSpectrum
        assert len(document.massSpectrum["xvals"]) == len(document.massSpectrum["yvals"])
        assert "xvals" in document.RT and "yvals" in document.RT
        assert len(document.RT["xvals"]) == len(document.RT["yvals"])
        assert "xvals" in document.DT and "yvals" in document.DT
        assert len(document.DT["xvals"]) == len(document.DT["yvals"])
