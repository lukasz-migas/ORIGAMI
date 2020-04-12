"""Config file for pytest"""
# Standard library imports
import os
import glob

# Third-party imports
import wx
import pytest

# Local imports
from origami.icons.icons import IconContainer
from origami.config.config import Config
from origami.utils.download import download_file
from origami.config.download import Download
from origami.utils.file_compression import unzip_directory

# To activate/deactivate certain things for pytest's only
# NOTE: Please leave this before any other import here!!
os.environ["ORIGAMI_PYTEST"] = "True"

dw_config = Download()

DATA_PATH = os.path.join(os.path.split(__file__)[0], "data")
DATA_WATERS_IM_SMALL = os.path.join(DATA_PATH, "WATERS_IM_SMALL.raw.zip")
DATA_TEXT_MS = os.path.join(DATA_PATH, "TEXT_MS.zip")
DATA_TEXT_HEATMAP = os.path.join(DATA_PATH, "TEXT_HEATMAP.zip")
DATA_THERMO_MS_SMALL = os.path.join(DATA_PATH, "THERMO_MS_SMALL.zip")


@pytest.fixture(scope="session", autouse=True)
def get_waters_im_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_WATERS_IM_SMALL):
        path = unzip_directory(DATA_WATERS_IM_SMALL, output_dir, False)
    else:
        link = dw_config["waters_raw_im"]
        path = download_file(link, output_dir=output_dir)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_thermo_ms_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_THERMO_MS_SMALL):
        path = unzip_directory(DATA_THERMO_MS_SMALL, output_dir, False)
    else:
        link = dw_config["thermo_raw_ms"]
        path = download_file(link, output_dir=output_dir)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_text_ms(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_TEXT_MS):
        path = unzip_directory(DATA_TEXT_MS, output_dir, False)
    else:
        link = dw_config["text_ms"]
        path = download_file(link, output_dir=output_dir)
    return glob.glob(os.path.join(path, "*"))


@pytest.fixture(scope="session", autouse=True)
def get_app():
    app = wx.App()
    frame = wx.Frame(None)
    frame.Show()

    config = Config()
    icons = IconContainer()

    return app, frame, config, icons
