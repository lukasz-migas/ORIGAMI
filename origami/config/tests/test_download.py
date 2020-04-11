# Standard library imports
import os

# Third-party imports
import pytest

# Local imports
from origami.config.download import Download


class TestDownload:
    def test_download(self):
        dw = Download()
        assert dw
        assert dw._loaded is True
        assert len(dw.links) > 0

        path = dw["text_ms"]
        assert isinstance(path, str)

        with pytest.raises(KeyError):
            _ = dw["not there"]

    def test_download_diff_cwd(self):
        path = os.path.dirname(os.getcwd())
        os.chdir(path)
        dw = Download()
        assert dw
        assert dw._loaded is True
        assert len(dw.links) > 0

        path = dw["text_ms"]
        assert isinstance(path, str)

        with pytest.raises(KeyError):
            _ = dw["not there"]
