"""Test config"""
# Standard library imports
import os
import logging

# Third-party imports
import pytest

# Local imports
from origami.config.config import Config


class TestConfig:
    def test_init(self):
        config = Config()
        assert config

        for i in range(10):
            cmap = config.get_random_colormap()
            assert isinstance(cmap, str)

        output = config.get_zoom_parameters()
        assert "normal" in output and "extract" in output

    def test_setup_temporary_dir(self, tmpdir_factory):
        config = Config()
        assert config

        cwd_path = str(tmpdir_factory.mktemp("Origami"))
        config.APP_CWD = cwd_path

        assert config.APP_TEMP_DATA_PATH is not None

        config.setup_temporary_dir()
        assert config.APP_TEMP_DATA_PATH is not None
        assert os.path.exists(config.APP_TEMP_DATA_PATH)

    @pytest.mark.parametrize("verbose", (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL))
    def test_setup_logging(self, tmpdir_factory, verbose):
        config = Config()
        assert config

        cwd_path = str(tmpdir_factory.mktemp("Origami"))
        config.APP_CWD = cwd_path

        assert config.APP_LOG_DIR is None

        config.setup_logging(verbose)
        assert config.APP_LOG_DIR is not None
        assert os.path.exists(config.APP_LOG_DIR)

        logger = logging.getLogger("origami")
        assert verbose == logger.getEffectiveLevel()

    def test_setup_paths(self):
        config = Config()
        assert config

        assert config.APP_DRIFTSCOPE_PATH is not None

        value = config.setup_paths(return_check=True)
        assert value is True
        assert os.path.exists(config.APP_DRIFTSCOPE_PATH)

    def test_save_load(self, tmpdir_factory):
        config = Config()

        path = str(tmpdir_factory.mktemp("config"))
        path = os.path.join(path, config.DEFAULT_CONFIG_NAME)
        assert path.endswith(".json")

        # save
        config.colorbar = False
        config.save_config(path)
        assert os.path.exists(path)

        # load
        config.colorbar = True
        config.load_config(path)
        assert config.colorbar is False

    def test_save_load_check_type(self, tmpdir_factory):
        config = Config()

        path = str(tmpdir_factory.mktemp("config"))
        path = os.path.join(path, config.DEFAULT_CONFIG_NAME)
        assert path.endswith(".json")

        # change some value
        config.colorbar = False

        # save
        config.save_config(path)
        assert os.path.exists(path)

        # load
        config.colorbar = "True"
        config.load_config(path)
        assert config.colorbar == "True"

        config.load_config(path, False)
        assert config.colorbar is False
