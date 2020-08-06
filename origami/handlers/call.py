"""Simple implementation of function caller"""
# Standard library imports
import sys
import time
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
        """
        if not callable(fcn):
            raise ValueError("You must provide a callable function as one of the arguments")

        # function to call in case of an error
        self.func_error = kwargs.pop("func_error", None)

        # function to call before the main function
        self.func_pre = kwargs.pop("func_pre", None)

        # main function
        self.func = fcn
        self.args = args
        self.kwargs = kwargs

        # function to call with the results
        self.func_result = kwargs.pop("func_result", None)
        self.func_result_args = kwargs.pop("func_result_args", ())
        self.func_result_kwargs = kwargs.pop("func_result_kwargs", dict())

        # function to call after the main function
        self.func_post = kwargs.pop("func_post", None)
        self.func_post_args = kwargs.pop("func_post_args", ())
        self.func_post_kwargs = kwargs.pop("func_post_kwargs", dict())

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def _wrap_results(self, results):
        if not isinstance(results, (list, tuple)):
            return (results,)
        return results

    # noinspection PyBroadException
    def run(self):
        """Run the object and ensure that results are returned and in case of errors, they are shown to the user"""
        # Retrieve args/kwargs here; and fire processing using them
        t_start = time.time()
        results = None
        try:
            self.on_pre()
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

        # post-run trigger
        self.on_post()
        return t_start

    def on_error(self, results):
        """If error does occur, try to return results to error handler"""
        if self.func_error:
            wx.CallAfter(self.func_error, *results)

    def on_result(self, results):
        """Return results back to the result handler"""
        if self.func_result:
            if results is None:
                results = ()
            if self.func_result_args is None:
                self.func_result_args = ()
            if self.func_result_kwargs is None:
                self.func_result_kwargs = {}
            wx.CallAfter(self.func_result, *results, *self.func_result_args, **self.func_result_kwargs)

    def on_pre(self):
        """If pre-call function was specified, notify it of having started the task"""
        if self.func_pre:
            wx.CallAfter(self.func_pre)

    def on_post(self):
        """If post-call function was specified, notify it of having finished the task"""
        if self.func_post:
            if self.func_post_args is None:
                self.func_post_args = ()
            if self.func_post_kwargs is None:
                self.func_post_kwargs = {}
            wx.CallAfter(self.func_post, *self.func_post_args, **self.func_post_kwargs)
