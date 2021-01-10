"""App directory configuration"""
# Standard library imports
import os

# Third-party imports
import appdirs

# Local imports
from origami import __version__
from origami.utils.path import make_directory

APP_NAME = "origami"
APP_AUTHOR = False

USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR, __version__)
if not os.path.exists(USER_DATA_DIR):
    make_directory(USER_DATA_DIR)

USER_CACHE_DIR = os.path.join(USER_DATA_DIR, "Cache")
USER_CONFIG_DIR = os.path.join(USER_DATA_DIR, "Configs")
USER_LOG_DIR = os.path.join(USER_DATA_DIR, "Logs")
USER_EXAMPLE_DIR = os.path.join(USER_DATA_DIR, "Data")

# ensure all of these exist
for path in [USER_CACHE_DIR, USER_CONFIG_DIR, USER_LOG_DIR, USER_EXAMPLE_DIR]:
    if not os.path.exists(path):
        make_directory(path)
