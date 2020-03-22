"""Configuration"""
# Standard library imports
import os

# Local imports
from origami.readers.io_json import read_json_data


class Download:
    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        try:
            self.links = read_json_data(os.path.join(path, "download.json"))
        except FileNotFoundError:
            self.links = dict()
            print("Failed to initilize download instance")

    def __getitem__(self, item):
        if item in self.links:
            return self.links[item]
        raise KeyError(f"Could not retrieve download link - try: {list(self.links.keys())}")
