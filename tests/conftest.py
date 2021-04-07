"""Config file for pytest"""
# Standard library imports
import os
import glob

# Third-party imports
import pytest

# Local imports
from origami.utils.download import download_file
from origami.config.download import Download
from origami.utils.file_compression import unzip_directory
import origami.utils.appdirs  # noqa

# To activate/deactivate certain things for pytest's only
# NOTE: Please leave this before any other import here!!
os.environ["ORIGAMI_PYTEST"] = "True"

dw_config = Download()

DATA_PATH = os.path.join(os.path.split(__file__)[0], "../_data")
if not os.path.exists(DATA_PATH):
    from origami.utils.path import make_directory

    make_directory(DATA_PATH)

# data paths
# raw
DATA_WATERS_IM_SMALL = os.path.join(DATA_PATH, "WATERS_IM_SMALL.raw.zip")
DATA_THERMO_MS_SMALL = os.path.join(DATA_PATH, "THERMO_MS_SMALL.zip")

# text
DATA_TEXT_ONE_MS = os.path.join(DATA_PATH, "TEXT_MS.zip")
DATA_TEXT_MANY_MS = os.path.join(DATA_PATH, "TEXT_MS.zip")
DATA_TEXT_HEATMAP = os.path.join(DATA_PATH, "TEXT_HEATMAP.zip")

# open format
DATA_MZML_MS_SMALL = os.path.join(DATA_PATH, "MZML_SMALL.zip")
DATA_MGF_MS_SMALL = os.path.join(DATA_PATH, "MGF_SMALL.zip")

# origami
DATA_ORIGAMI_IM = os.path.join(DATA_PATH, "DOCUMENT.origami.zip")


@pytest.fixture(scope="session", autouse=True)
def get_waters_im_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_WATERS_IM_SMALL):
        path = unzip_directory(DATA_WATERS_IM_SMALL, output_dir, False)
    else:
        link = dw_config["waters_raw_im"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_thermo_ms_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_THERMO_MS_SMALL):
        path = unzip_directory(DATA_THERMO_MS_SMALL, output_dir, False)
    else:
        link = dw_config["thermo_raw_ms"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_mgf_ms_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_MGF_MS_SMALL):
        path = unzip_directory(DATA_MGF_MS_SMALL, output_dir, False)
    else:
        link = dw_config["mgf_ms"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_mzml_ms_small(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_MZML_MS_SMALL):
        path = unzip_directory(DATA_MZML_MS_SMALL, output_dir, False)
    else:
        link = dw_config["mzml_ms"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_text_ms_path(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_TEXT_ONE_MS):
        path = unzip_directory(DATA_TEXT_ONE_MS, output_dir, False)
    else:
        link = dw_config["text_one_ms"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    paths = glob.glob(os.path.join(path, "*"))
    return paths[0]


@pytest.fixture(scope="session", autouse=True)
def get_text_ms_paths(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_TEXT_MANY_MS):
        path = unzip_directory(DATA_TEXT_MANY_MS, output_dir, False)
    else:
        link = dw_config["text_many_ms"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return glob.glob(os.path.join(path, "*"))


@pytest.fixture(scope="session", autouse=True)
def get_origami_document(tmpdir_factory):
    """Create folder with processed data for testing purposes"""
    output_dir = str(tmpdir_factory.mktemp("data"))
    if os.path.exists(DATA_ORIGAMI_IM):
        path = unzip_directory(DATA_ORIGAMI_IM, output_dir, False)
    else:
        link = dw_config["origami_im"]
        path = download_file(link, output_dir=output_dir, copy_to_dir=DATA_PATH)
    return os.path.abspath(path)


@pytest.fixture(scope="session", autouse=True)
def get_env_with_document(get_origami_document):
    """Get pre-loaded document"""
    from origami.config.environment import ENV

    ENV.load(get_origami_document)
    title = ENV.current
    return ENV, title