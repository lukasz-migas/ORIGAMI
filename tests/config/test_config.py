"""Test config"""
# Standard library imports
import os

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

    def test_save_load(self, tmpdir_factory):
        config = Config()

        path = str(tmpdir_factory.mktemp("config"))
        path = os.path.join(path, config.DEFAULT_CONFIG_NAME)
        assert path.endswith(".json")

        # change some value
        config.colorbar = False

        # save
        config.save_config(path)
        assert os.path.exists(path)
        assert config.colorbar is False

        config.colorbar = True

        # load
        config.load_config(path)
        assert config.colorbar is False
