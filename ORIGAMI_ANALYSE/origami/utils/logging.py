"""Define py logger"""
import logging
import sys

__all__ = ['set_logger_level', 'set_logger']

logger = logging.getLogger("specML")

LOGGING_TYPES = dict(DEBUG=logging.DEBUG, INFO=logging.INFO, WARNING=logging.WARNING, ERROR=logging.ERROR,
                     CRITICAL=logging.CRITICAL)


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

    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] - %(levelname)s - %(message)s',
        handlers=handlers,
        datefmt='%m/%d/%Y %I:%M:%S')


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

    logger = logging.getLogger('py')

    if verbose is None:
        verbose = "INFO"
    if isinstance(verbose, bool):
        verbose = 'INFO' if verbose else 'WARNING'
    if isinstance(verbose, str):
        if (verbose.upper() in LOGGING_TYPES):
            verbose = verbose.upper()
            verbose = LOGGING_TYPES[verbose]
            logger.setLevel(verbose)
        else:
            raise ValueError("verbose must be in "
                             "{}".format(', '.join(LOGGING_TYPES)))
