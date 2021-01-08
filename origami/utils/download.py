"""Download files from dropbox."""
# Standard library imports
import os
import sys
import logging
from typing import Optional
from urllib import request

# Local imports
from origami.utils.path import copy_file
from origami.utils.file_compression import unzip_directory

LOGGER = logging.getLogger(__name__)

__all__ = ["download_file"]


# This module was taken and slightly modified from https://github.com/EtienneCmb/visbrain


def reporthook(block_num, block_size, total_size):
    """Report downloading status."""
    read_size = block_num * block_size
    if total_size > 0:
        percent = min(100, read_size * 1e2 / total_size)
        s = "\rSTATUS : %5.1f%% %*d / %d" % (percent, len(str(total_size)), read_size, total_size)
        sys.stderr.write(s)
        if read_size >= total_size:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("\rread %d" % (read_size,))


def download_file(
    name,
    filename=None,
    output_dir=None,
    unzip=True,
    remove_archive=False,
    use_pwd=True,
    copy_to_dir: Optional[str] = None,
):
    """Download a file.

    By default this function download a file to ~/explorer_data.

    Parameters
    ----------
    name : str
        Name of the file to download or url.
    filename : str
        Name of the file to be saved in case of url.
    output_dir : str
        Download file to the path specified.
    unzip : bool
        Unzip archive if needed.
    remove_archive : bool
        Remove archive after unzip.
    use_pwd : bool
        Download the file to the current directory.
    copy_to_dir : str, optional
        directory where to copy the zipped file

    Returns
    -------
    path_to_file : string
        Path to the downloaded file.
    """
    # default is the home path
    out_path = os.getcwd() if use_pwd else os.path.join(os.path.expanduser("~"), "example-data")
    if "http" in name:
        if filename is None:
            filename = os.path.split(name)[1]
            if "?" in filename:
                filename = filename.split("?")[0]
        assert isinstance(filename, str)
        url = name
    else:
        raise ValueError("Expected a link!")

    output_dir = out_path if not isinstance(output_dir, str) else output_dir
    path_to_file = os.path.join(output_dir, filename)
    to_download = not os.path.isfile(path_to_file)

    # download file if needed
    if to_download:
        LOGGER.info("Downloading %s" % path_to_file)
        # Check if directory exists else creates it
        if not os.path.exists(output_dir):
            LOGGER.info("Folder %s created" % output_dir)
            os.makedirs(output_dir)
        # Download file :
        _, _ = request.urlretrieve(url, path_to_file, reporthook=reporthook)
    else:
        LOGGER.info("File already downloaded (%s)." % path_to_file)

    # copy
    if copy_to_dir:
        basename = os.path.basename(path_to_file)
        copy_file(path_to_file, os.path.join(copy_to_dir, basename))

    # Unzip file :
    if unzip:
        path_to_file = unzip_directory(path_to_file, output_dir, remove_archive)

    LOGGER.info("Downloaded (%s)." % path_to_file)

    return path_to_file
