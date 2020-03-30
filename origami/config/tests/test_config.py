# Local imports
from origami.config.config import Config


class TestConfig:
    @staticmethod
    def test_init():
        config = Config()
        assert config
