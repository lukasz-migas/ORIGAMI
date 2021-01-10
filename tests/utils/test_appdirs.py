"""Test appdirs"""
from origami.utils.appdirs import USER_DATA_DIR, USER_CACHE_DIR, USER_CONFIG_DIR, USER_LOG_DIR, USER_EXAMPLE_DIR
import os


class TestAppdirs:
    def test_dirs_exist(self):
        for path in [USER_DATA_DIR, USER_CACHE_DIR, USER_CONFIG_DIR, USER_LOG_DIR, USER_EXAMPLE_DIR]:
            assert os.path.exists(path)
