"""Test origami.readers.io_waters_raw.py"""
# Local imports
from origami.readers.io_text_files import TextSpectrumReader


class TestTextSpectrumReader:
    @staticmethod
    def test_one_spectrum(get_text_ms):
        for path in get_text_ms:
            reader = TextSpectrumReader(path)
            assert len(reader.x) == len(reader.y)
            assert reader.ys is None
            assert reader.n_spectra == 1
