# Standard library imports
import os
import logging
import zipfile

LOGGER = logging.getLogger(__name__)


def unzip_directory(path_to_zip: str, output_dir: str, remove_archive: bool = True):
    LOGGER.debug("Unzipping directory...")
    # unzip archive
    zip_file_object = zipfile.ZipFile(path_to_zip, "r")
    zip_file_object.extractall(path=output_dir)
    path_to_file = os.path.join(output_dir, zip_file_object.namelist()[0])
    zip_file_object.close()
    LOGGER.debug("Unzipped directory")

    if remove_archive:  # Remove archive :
        LOGGER.debug("Archive %s removed" % path_to_zip)
        os.remove(path_to_zip)

    return path_to_file
