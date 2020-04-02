"""Decorators"""
# Standard library imports
from sys import platform

# Local imports
from origami.utils.time import ttime
from origami.utils.logging import get_logger

LOGGER = get_logger("DEBUG")


def signal_blocker(fcn):
    def wrapped(self, *args, **kwargs):
        if not hasattr(self, "_block"):
            out = fcn(self, *args, **kwargs)
            return out
        self._block = True
        out = fcn(self, *args, **kwargs)
        self._block = False
        return out

    return wrapped


def check_os(*os):
    """Check whether this function can be executed on the current OS

    Parameters
    ----------
    os :
        allowed operating system(s)

    Raises
    ------
    AssertionError
        if current OS is not listed, assertion error will be raised
    """

    def _check_os(f):
        def new_f(*args, **kwargs):
            assert platform in os, f"Cannot perform action on this operating system ({platform}) - try again on `{os}`"
            return f(*args, **kwargs)

        new_f.__name__ = f.__name__
        return new_f

    return _check_os


def Timer(fcn):
    def timer(self, *args, **kwargs):
        tstart = ttime()
        out = fcn(self, *args, **kwargs)
        LOGGER.debug(f"Function `{fcn.__name__}` took {ttime()-tstart:.4f}s to execute")

        return out

    return timer
