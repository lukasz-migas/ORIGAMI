import os
from utils.converters import byte2str

import logging
logger = logging.getLogger("specML")

__all__ = ["get_path_and_fname", "clean_up_folder", "check_waters_path"]


def get_path_and_fname(path, simple=False):
    """
    Retrieve file path and filename. Also check whether path exists.
    path: str
        file path
    simple: bool
        only return path (without filename) and filename
    """

    # strip file extension from path name
    if path.endswith((".hdi", ".imzML", ".raw", ".pickle")):
        path, _ = os.path.splitext(path)

    full_path = path
    path, fname = os.path.split(path)
    fname, _ = os.path.splitext(fname)
    is_path = os.path.isdir(path)

    if simple:
        return path, byte2str(fname)

    return full_path, path, fname, is_path


def clean_up_folder(filepath):
    try:
        os.remove(filepath)
    except Exception as e:
        logger.warning(e)


def check_waters_path(filepath):
    if not filepath.endswith(".raw"):
        filepath = filepath + ".raw"

    return filepath
