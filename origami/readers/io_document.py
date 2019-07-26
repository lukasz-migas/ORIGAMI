# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import copy
import logging
import pickle
import time

logger = logging.getLogger("origami")


def save_py_object(filename=None, saveFile=None):
    """
    Simple tool to save objects/dictionaries
    """
    tstart = time.time()
    logger.info("Saving document...")
    with open(filename, "wb") as handle:
        saveFile, restore_kwargs = cleanup_document(saveFile)
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)

    saveFile = restore_document(saveFile, **restore_kwargs)
    logger.info(f"Saved document in: {filename}. It took {time.time()-tstart:.4f} seconds.")


def open_py_object(filename=None):
    """
    Simple tool to open pickled objects/dictionaries
    """
    if filename.rstrip("/")[-7:] == ".pickle":
        with open(filename, "rb") as f:
            try:
                return pickle.load(f)
            except Exception as e:
                print(e)
                return None
    else:
        with open(filename + ".pickle", "rb") as f:
            return pickle.load(f)


def cleanup_document(document):

    restore_kwargs = dict()
    if "temporary_unidec" in document.massSpectrum:
        temporary_unidec = copy.deepcopy(document.massSpectrum.pop("temporary_unidec"))
        restore_kwargs["massSpectrum"] = temporary_unidec

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

    if "file_reader" in kwargs:
        document.file_reader = kwargs.pop("file_reader")

    for spectrum in kwargs:
        document.multipleMassSpectrum[spectrum]["temporary_unidec"] = kwargs.pop(spectrum)

    return document
