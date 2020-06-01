"""Misc containers"""
# Standard library imports
from collections import namedtuple

FileItem = namedtuple("FileItem", ["variable", "path", "scan_range", "mz_range", "im_on", "information"])
