"""Simple implementation of function caller"""
# Standard library imports
import sys
import logging
import traceback
from builtins import isinstance

# Third-party imports
import wx

LOGGER = logging.getLogger(__name__)


class Call:
    def __init__(self, fcn, *args, **kwargs):
        """Simple callable object that can be used by multi-threading Queue

        Parameters
        ----------
        fcn : Callable
        args
        kwargs
        """
        # retrieve keyword parameters
        self.func_call_result = kwargs.pop("func_result", None)
        self.func_call_result_kwargs = kwargs.pop("func_result_kwargs", dict())
        self.func_call_error = kwargs.pop("func_error", None)
        self.func_call_post = kwargs.pop("func_post", None)
        self.func_call_pre = kwargs.pop("func_pre", None)

        if not callable(fcn):
            raise ValueError("You must provide a callable function as one of the arguments")

        # fcn attributes
        self.func = fcn
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    # noinspection PyBroadException
    def run(self):
        """Run the object and ensure that results are returned and in case of errors, they are shown to the user"""
        # Retrieve args/kwargs here; and fire processing using them
        results = None
        try:
            self.on_pre(None)
            results = self.func(*self.args, **self.kwargs)
            results = self._wrap_results(results)
        except Exception:
            traceback.print_exc()
            exc_type, value = sys.exc_info()[:2]
            self.on_error((exc_type, value, traceback.format_exc()))
            LOGGER.error(f"{exc_type} ; {value} ; {traceback.format_exc()}")
            return
        finally:
            self.on_result(results)
        self.on_post(results)

    def on_error(self, results):
        """If error does occur, try to return results to error handler"""
        if self.func_call_error:
            wx.CallAfter(self.func_call_error, *results)

    def on_result(self, results):
        """Return results back to the result handler"""
        if self.func_call_result:
            wx.CallAfter(self.func_call_result, *results)

    def on_pre(self, results):
        """If pre-call function was specified, notify it of having started the task"""
        if self.func_call_pre:
            wx.CallAfter(self.func_call_pre, *results)

    def on_post(self, results):
        """If post-call function was specified, notify it of having finished the task"""
        if self.func_call_post:
            wx.CallAfter(self.func_call_post, *results)

    def _wrap_results(self, results):
        if not isinstance(results, (list, tuple)):
            return (results,)
        return results
