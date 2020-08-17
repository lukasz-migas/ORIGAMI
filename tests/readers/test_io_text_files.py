"""Test origami.readers.io_waters_raw.py"""
# Local imports
from origami.readers.io_text_files import TextSpectrumReader


class TestTextSpectrumReader:
    @staticmethod
    def test_one_spectrum(get_text_ms_paths):
        for path in get_text_ms_paths:
            reader = TextSpectrumReader(path)
            assert len(reader.x) == len(reader.y)
            assert reader.ys is None
            assert reader.n_spectra == 1
