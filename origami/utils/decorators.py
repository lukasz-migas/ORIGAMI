"""Decorators"""
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


def Timer(fcn):
    def timer(self, *args, **kwargs):
        tstart = ttime()
        out = fcn(self, *args, **kwargs)
        LOGGER.debug(f"Function `{fcn.__name__}` took {ttime()-tstart:.4f}s to execute")

        return out

    return timer
