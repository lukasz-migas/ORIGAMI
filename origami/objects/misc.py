"""Misc containers"""
# Standard library imports
from collections import namedtuple

FileItem = namedtuple("FileItem", ["variable", "path", "scan_range", "mz_range", "im_on", "information"])


class CompareItem:
    """Spectrum comparison object"""

    __slots__ = ["document", "title", "legend"]

    def __init__(self, document: str = None, title: str = None, legend: str = None):
        self.document = document
        self.title = title
        self.legend = legend
