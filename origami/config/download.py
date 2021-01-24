"""Configuration"""
# Standard library imports
import os

# Local imports
from origami.readers.io_json import read_json_data

LINKS = {
    "waters_raw_im": "https://www.dropbox.com/s/6un130m2c7n6fwd/WATERS_IM_SMALL.raw.zip?dl=1",
    "text_ms": "https://www.dropbox.com/s/afgvw1r8tco27zc/TEXT_MS.zip?dl=1",
    "thermo_raw_ms": "https://www.dropbox.com/s/2evl75s53tcabjc/THERMO_MS_SMALL.zip?dl=1",
    "mzml_ms": "https://www.dropbox.com/s/qqpsikwdx4eojrh/MZML_SMALL.zip?dl=1",
    "mgf_ms": "https://www.dropbox.com/s/dtc0qw1ki11ddk0/MGF_SMALL.zip?dl=1",
}


class Download:
    """Download"""

    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self._json_path = os.path.join(path, "download.json")
        try:
            self.links = read_json_data(self._json_path)
            self._loaded = True
        except FileNotFoundError:
            self.links = LINKS
            self._loaded = False
            print("Failed to initialize download instance")

    def __getitem__(self, item):
        if item in self.links:
            return self.links[item]
        raise KeyError(
            f"Could not retrieve download link - try: {list(self.links.keys())}"
            f" [config: {self._json_path}; loaded={self._loaded}]"
        )
