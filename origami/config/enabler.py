"""Enabler class"""
# Standard library imports
import sys


class AppEnabler:
    """Class used to determine which menu items, actions, functions, etc... should be allowed on different OS"""

    def __init__(self):
        self.PLATFORM = sys.platform
        self.IS_WINDOWS = sys.platform == "win32"
        self.IS_LINUX = sys.platform == "linux"
        self.IS_MAC = sys.platform == "darwin"

        self.ALLOW_WATERS_EXTRACTION = self.IS_WINDOWS
        self.ALLOW_THERMO_EXTRACTION = self.IS_WINDOWS
        self.ALLOW_UNIDEC = self.IS_WINDOWS


APP_ENABLER: AppEnabler = AppEnabler()
