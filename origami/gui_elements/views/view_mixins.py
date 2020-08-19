"""Mixins used by various views in the application"""
# Standard library imports
import time
import logging
from abc import ABC
from copy import copy

# Local imports
from origami.config.config import CONFIG
from origami.utils.utilities import report_time

LOGGER = logging.getLogger(__name__)


class ViewWaterfallMixin(ABC):
    """Mixin class for Waterfall-based plots

    This class should not be instantiated separately and requires several attributes and functions to work
    """

    def plot_waterfall(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""
        self.can_plot("waterfall")  # noqa
        t_start = time.time()
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)  # noqa
        mpl_keys.append("waterfall")

        self.set_document(obj, **kwargs)  # noqa
        self.set_labels(obj, **kwargs)  # noqa

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs.update(**self.FORCED_KWARGS)  # noqa
        kwargs = self.check_kwargs(**kwargs)  # noqa
        x, y, array = self.check_input(x, y, array, obj)  # noqa
        self.figure.clear()  # noqa
        self.figure.plot_waterfall(  # noqa
            x,
            y,
            array,
            x_label=self.y_label,  # noqa
            y_label="Offset intensity",
            callbacks=self._callbacks,  # noqa
            obj=obj,
            **kwargs,  # noqa
        )
        if repaint:
            self.figure.repaint()  # noqa

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)  # noqa
        self.set_plot_parameters(**kwargs)  # noqa
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def _update_style_waterfall(self, name: str):
        """Update Waterfall style"""
        if not self.is_plotted_or_plot("waterfall", self.plot_waterfall, self.DATA_KEYS):  # noqa
            return
        kwargs = dict()
        # update data - requires full redraw
        if name.endswith(".data"):
            self.replot("waterfall", False)  # noqa
        else:
            kwargs = CONFIG.get_mpl_parameters(["waterfall"])
            x, y, array = self.get_data(["x", "y", "array"])  # noqa
            self.figure.plot_waterfall_update(x, y, array, name, **kwargs)  # noqa
        return kwargs


class ViewViolinMixin(ABC):
    """Mixin class for Violin-based plots

    This class should not be instantiated separately and requires several attributes and functions to work
    """

    def plot_violin(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a violin plot"""
        self.can_plot("violin")  # noqa
        t_start = time.time()
        mpl_keys = copy(self.MPL_KEYS)  # noqa
        mpl_keys.append("violin")

        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)  # noqa
        self.set_labels(obj, **kwargs)  # noqa

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs.update(**self.FORCED_KWARGS)  # noqa
        kwargs = self.check_kwargs(**kwargs)  # noqa
        x, y, array = self.check_input(x, y, array, obj)  # noqa
        self.figure.clear()  # noqa
        self.figure.plot_violin_quick(  # noqa
            x,
            y,
            array,
            x_label=self.x_label,  # noqa
            y_label=self.y_label,  # noqa
            callbacks=self._callbacks,  # noqa
            obj=obj,
            **kwargs,
        )
        if repaint:
            self.figure.repaint()  # noqa

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)  # noqa
        self.set_plot_parameters(**kwargs)  # noqa
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def _update_style_violin(self, name: str):
        """Update violin style"""
        if not self.is_plotted_or_plot("violin", self.plot_violin, self.DATA_KEYS):  # noqa
            return

        kwargs = dict()
        # update data - requires full redraw
        if name.endswith(".data"):
            self.replot("violin", False)  # noqa
        else:
            kwargs = CONFIG.get_mpl_parameters(["violin"])
            x, y, array = self.get_data(["x", "y", "array"])  # noqa
            self.figure.plot_violin_update(x, y, array, name, **kwargs)  # noqa
        return kwargs


class ViewAxesMixin(ABC):
    """Mixin class for plot axes and labels

    This class should not be instantiated directly and requires several attributes and functions to work
    """

    def _update_style_axes(self, name: str):
        """Update axes"""

        kwargs = CONFIG.get_mpl_parameters(["axes"])
        if name.endswith(".frame"):
            self.figure.plot_update_frame(**kwargs)  # noqa
        elif name.endswith(".labels"):
            self.figure.plot_update_labels(**kwargs)  # noqa
        return kwargs
