# Standard library imports
import os
import re
import shutil
import string
import logging
import unicodedata
from collections.abc import Iterable

# Local imports
from origami.utils.converters import byte2str

LOGGER = logging.getLogger(__name__)

VALID_FILENAME_CHARACTERS = "-_.() %s%s" % (string.ascii_letters, string.digits)
CHARACTER_LIMIT = 255


def make_directory(path: str):
    """Make directory"""
    try:
        os.makedirs(path)
    except FileExistsError:
        LOGGER.debug("Could not create directory")


def move_directory_contents(path):
    """Recursively move files to a new location"""


def get_delimiter_from_filename(path):
    """Get delimiter based on the filename"""
    if path.endswith("csv"):
        return ","
    if path.endswith("txt"):
        return " "
    if path.endswith("tab"):
        return "\t"
    return ","


def get_duplicate_name(name: str, split_str: str = None, suffix: str = "copy"):
    """Get alternative name for an object

    Parameters
    ----------
    name : str
        initial name to be checked
    split_str : str, optional
        value by which the name should be split, e.g. can be file extension such as `.origami`
    suffix : str
        suffix to be added to the filename

    Returns
    -------
    name : str
        new name with `copy N` appended to it
    """
    if split_str is not None:
        name = name.split(split_str)[0]

    prev = re.findall(rf"\({suffix} (\d+)", name)
    n = 0

    if prev:
        n = int(prev[-1])

    while f" ({suffix} %d)" % n in name:
        n += 1

    if n == 0:
        name = name + f" ({suffix} %d)" % n
    else:
        name = name.replace(f" ({suffix} {n-1})", f" ({suffix} {n})")

    if split_str is not None:
        name += split_str

    return name


def clean_filename(filename, whitelist=VALID_FILENAME_CHARACTERS, replace=False):
    """Clean-up filename so it complies with Windows-naming scheme"""
    # replace spaces
    if replace and isinstance(replace, Iterable):
        for r in replace:
            filename = filename.replace(r, "_")

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode()

    # replace multiple whitespaces
    cleaned_filename = " ".join(cleaned_filename.split())

    # keep only whitelisted chars
    cleaned_filename = "".join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > CHARACTER_LIMIT:
        print(
            "Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(
                CHARACTER_LIMIT
            )
        )
    return cleaned_filename[:CHARACTER_LIMIT]


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
    """Clean-up folder"""
    try:
        os.remove(filepath)
    except Exception as e:
        LOGGER.warning(e)


def check_waters_path(filepath):
    """Check if is waters path"""
    if not filepath.endswith(".raw"):
        filepath = filepath + ".raw"

    return filepath


def check_path_exists(path):
    """Checks whether directory exists"""
    if path is None:
        return False
    return os.path.isdir(path)


def check_file_exists(path):
    """Checks whether file exists"""
    return os.path.isfile(path)


def clean_up_MDD_path(path):
    """The path(s) that return from MDD panel are not standard hence need to be cleaned-up"""
    try:
        path_split = path.split(":)")
        drive = path_split[0].split("(")
        drive = drive[-1]
        path = "{}:{}".format(drive, path_split[1])
    except IndexError:
        path = path
    return path


def get_base_path(filepath):
    """Get base path of the filepath"""
    return os.path.dirname(filepath)


def copy_file(from_file: str, to_path: str):
    """Copy file to new location"""
    shutil.copyfile(from_file, to_path)


def copy_directory(from_path, to_path, overwrite: bool = False):
    """Copy directory to a new location"""
    if os.path.exists(to_path):
        if overwrite:
            shutil.rmtree(to_path)
        else:
            raise OSError("Cannot copy directory to this location because the destination directory is not empty!")
    shutil.copytree(from_path, to_path)


def move_directory(from_path, to_path, overwrite: bool = False):
    """Move directory to new location"""
    copy_directory(from_path, to_path, overwrite)
    shutil.rmtree(from_path)


def clean_directory(dir_path):
    """Iterate over specified directory and delete all files and directories"""
    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        # remove directory
        try:
            shutil.rmtree(filepath)
        # remove files
        except OSError:
            try:
                os.remove(filepath)
            except Exception:
                continue


def get_subdirectories(path, extensions=None, as_short=True):
    """Get list of directories"""

    def _append():
        if as_short:
            subdirectories.append(dirpath)
        else:
            subdirectories.append(_dirpath)

    # if extensions is None:
    #     extensions = []

    if extensions is not None and not isinstance(extensions, (list, tuple)):
        extensions = [extensions]

    subdirectories = []
    for dirpath in os.listdir(path):
        _dirpath = os.path.join(path, dirpath)
        if os.path.isdir(_dirpath):
            if extensions is not None:
                for extension in extensions:
                    if _dirpath.endswith(extension):
                        _append()
            else:
                _append()
    return subdirectories
