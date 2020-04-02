# Standard library imports
import sys
import copy
import time
import pickle
import logging

# Local imports
from origami.utils.path import check_file_exists

logger = logging.getLogger(__name__)


def save_py_object(filename=None, saveFile=None):
    """Save document / object(s) as pickled file"""
    tstart = time.time()
    logger.info("Saving document...")
    with open(filename, "wb") as handle:
        saveFile, restore_kwargs = cleanup_document(saveFile)
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)

    saveFile = restore_document(saveFile, **restore_kwargs)
    logger.info(f"Saved document in: {filename}. It took {time.time()-tstart:.4f} seconds.")


def open_py_object(filename):
    """Load pickled document

    Parameters
    ----------
    filename : str
        path to the pickled object

    Returns
    -------
    document : document object
    """
    if check_file_exists(filename):
        with open(filename, "rb") as f:
            # try loading as python 3
            try:
                return pickle.load(f), 2
            except Exception as err:
                # try loading as python 2
                try:
                    return pickle.load(f, encoding="latin1"), 1
                except Exception as err:
                    # try loading as python 2 with wxPython2 support
                    try:
                        from wx import _core

                        sys.modules["wx._gdi"] = _core
                        return pickle.load(f, encoding="latin1"), 1
                    # try loading as python 2 with wxPython2 support and correct MARK location
                    except Exception as err:
                        logger.error(err)
                        try:
                            f.seek(0)
                            return pickle.load(f, encoding="latin1"), 1
                        # give up...
                        except Exception as err:
                            logger.error(err)
                            return None


def cleanup_document(document):
    """Remove some of the temporary elements - some cannot be pickled/deep copied"""

    restore_kwargs = dict()
    if "temporary_unidec" in document.massSpectrum:
        temporary_unidec = copy.deepcopy(document.massSpectrum.pop("temporary_unidec"))
        restore_kwargs["massSpectrum"] = temporary_unidec

    if "temporary_unidec" in document.smoothMS:
        temporary_unidec = copy.deepcopy(document.smoothMS.pop("temporary_unidec"))
        restore_kwargs["smoothMassSpectrum"] = temporary_unidec

    for spectrum in document.multipleMassSpectrum:
        if "temporary_unidec" in document.multipleMassSpectrum[spectrum]:
            temporary_unidec = copy.deepcopy(document.multipleMassSpectrum[spectrum].pop("temporary_unidec"))
            restore_kwargs[spectrum] = temporary_unidec

    try:
        file_reader = document.file_reader
        restore_kwargs["file_reader"] = file_reader
        document.file_reader = {}
    except Exception as err:
        logger.warning(err)

    return document, restore_kwargs


def restore_document(document, **kwargs):

    if "massSpectrum" in kwargs:
        document.massSpectrum["temporary_unidec"] = kwargs.pop("massSpectrum")

    if "smoothMassSpectrum" in kwargs:
        document.smoothMS["temporary_unidec"] = kwargs.pop("smoothMassSpectrum")

    if "file_reader" in kwargs:
        try:
            document.file_reader = kwargs.pop("file_reader")
        except:
            logger.warning("Failed to re-add `file_reader` to the document")

    kwargs_names = list(kwargs.keys())
    for spectrum in kwargs_names:
        try:
            document.multipleMassSpectrum[spectrum]["temporary_unidec"] = kwargs.pop(spectrum)
        except KeyError:
            logger.warning(f"Failed to re-add `{spectrum}` to the document")

    return document


def duplicate_document(document):
    """Duplicate document without affecting underlying data"""
    document, restore_kwargs = cleanup_document(document)
    document_copy = copy.deepcopy(document)

    # restore
    _ = restore_document(document, **restore_kwargs)
    document_copy = restore_document(document_copy, **restore_kwargs)

    return document_copy
