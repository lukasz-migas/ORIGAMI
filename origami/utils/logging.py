# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Define ORIGAMI logger"""
import logging
import sys

__all__ = ["set_logger_level", "set_logger"]

logger = logging.getLogger("origami")

LOGGING_TYPES = dict(
    DEBUG=logging.DEBUG, INFO=logging.INFO, WARNING=logging.WARNING, ERROR=logging.ERROR, CRITICAL=logging.CRITICAL
)
FMT = "[%(asctime)s] [%(levelname)s] [%(process)d] [%(filename)s:%(lineno)s:%(funcName)s] %(message)s"


def delete_logger():
    """Deletes all loggers"""
    # in case other logger has already set these
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


def set_logger_parameters(verbose, filepath=None):
    """Set logger level"""

    set_logger_level(verbose)
    set_logger_format(filepath)


def get_logger(verbose):
    LOGGER = logging.getLogger("origami")
    set_logger_parameters(verbose)
    return LOGGER


def set_logger(file_path=None):
    """
    Setup logger

    Parameters
    ----------
    file_path: str
        valid path where logger can write messages
    """

    file_handler = logging.FileHandler(filename=file_path)
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    fmt = "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(lineno)s:%(filename)s:%(funcName)s] - %(message)s"

    logging.basicConfig(level=logging.DEBUG, format=fmt, handlers=handlers, datefmt="%Y-%m-%d %H:%M:%S")


def set_logger_format(filepath=None):

    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [stdout_handler]
    if filepath is not None:
        file_handler = logging.FileHandler(filename=filepath)
        handlers.extend([file_handler])

    logging.basicConfig(level=logging.DEBUG, handlers=handlers, format=FMT, datefmt="%Y-%m-%d %H:%M:%S")


def set_logger_level(verbose=None):
    """Convenience function for setting the logging level.

    This function comes from the PySurfer package. See :
    https://github.com/nipy/PySurfer/blob/master/surfer/utils.py

    Parameters
    ----------
    verbose : bool, str, int, or None
        The verbosity of messages to print. If a str, it can be either
        PROFILER, DEBUG, INFO, WARNING, ERROR, or CRITICAL.
    """

    logger = logging.getLogger("origami")

    if verbose is None:
        verbose = "INFO"
    if isinstance(verbose, bool):
        verbose = "INFO" if verbose else "WARNING"
    if isinstance(verbose, str):
        if verbose.upper() in LOGGING_TYPES:
            verbose = verbose.upper()
            verbose = LOGGING_TYPES[verbose]
            logger.setLevel(verbose)
        else:
            raise ValueError("verbose must be in " "{}".format(", ".join(LOGGING_TYPES)))
