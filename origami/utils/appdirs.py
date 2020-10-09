"""App directory configuration"""
# Third-party imports
import appdirs

# Local imports
from origami import __version__

APP_NAME = "origami"
APP_AUTHOR = False

USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR, __version__)
USER_CACHE_DIR = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR, __version__)
USER_CONFIG_DIR = appdirs.user_config_dir(APP_NAME, APP_AUTHOR, __version__)
USER_LOG_DIR = appdirs.user_log_dir(APP_NAME, APP_AUTHOR, __version__)
