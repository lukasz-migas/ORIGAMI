# Standard library imports
import sys

# Third-party imports
import pytest

# Local imports
from origami.document import document as Document
from origami.handlers.load import LoadHandler

# enable on windowsOS only
if sys.platform == "win32":
    from origami.readers.io_waters_raw import WatersIMReader
    from origami.readers.io_waters_raw_api import WatersRawReader


@pytest.fixture
def load_handler():
    return LoadHandler()


class TestLoadHandler:
    def test_init(self):
        _load_handler = LoadHandler()
        assert _load_handler

    def test_waters_extract_ms_from_mobilogram(self, get_waters_im_small):
        assert True

    def test_waters_extract_ms_from_chromatogram(self):
        assert True

    def test_waters_extract_heatmap_from_mass_spectrum_one(self):
        assert True

    def test_waters_extract_heatmap_from_mass_spectrum_many(self):
        assert True

    def test_waters_im_extract_ms(self):
        assert True

    def test_waters_im_extract_rt(self):
        assert True

    def test_waters_im_extract_dt(self):
        assert True

    def test_waters_im_extract_heatmap(self):
        assert True

    def test_waters_im_extract_msdt(self):
        assert True

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

    def test_load_thermo_data(self):
        assert True

    def test_load_thermo_document(self):
        assert True

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
