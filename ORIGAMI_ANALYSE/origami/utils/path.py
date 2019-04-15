import os
from utils.converters import byte2str

import logging
logger = logging.getLogger("origami")

__all__ = ["get_path_and_fname", "clean_up_folder", "check_waters_path", "check_path_exists", "check_file_exists"]


def get_path_and_fname(path, simple=False):
    """
    Retrieve file path and filename. Also check whether path exists.
    path: str
        file path
    simple: bool
        only return path (without filename) and filename
    """

    # strip file extension from path name
    if path.endswith((".hdi", ".imzML", ".raw", ".pickle", ".csv", ".txt", ".RAW", ".mzML", ".mgf")):
        path, _ = os.path.splitext(path)

    full_path = path
    path, fname = os.path.split(path)
    fname, _ = os.path.splitext(fname)
    is_path = os.path.isdir(path)

    if simple:
        return path, byte2str(fname)

    return full_path, path, fname, is_path


def get_path_and_extension(path):
    return os.path.splitext(path)


def clean_up_folder(filepath):
    try:
        os.remove(filepath)
    except Exception as e:
        logger.warning(e)


def check_waters_path(filepath):
    if not filepath.endswith(".raw"):
        filepath = filepath + ".raw"

    return filepath


def check_path_exists(path):
    return os.path.isdir(path)


def check_file_exists(path):
    return os.path.isfile(path)


def clean_up_MDD_path(path):
    """The path(s) that return from MDD panel are not standard hence need to be cleaned-up"""
    try:
        path_split = path.split(':)')
        drive = path_split[0].split('(')
        drive = drive[-1]
        path = "{}:{}".format(drive, path_split[1])
    except IndexError:
        path = path
    return path
