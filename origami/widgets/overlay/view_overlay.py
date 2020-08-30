"""Visualisation view"""
# Standard library imports
import time
import logging
from copy import copy

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.visuals.mpl.plot_overlay import PlotOverlay
# from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin
from origami.gui_elements.views.view_mixins import ViewAxesMixin
from origami.gui_elements.views.view_mixins import ViewWaterfallMixin

LOGGER = logging.getLogger(__name__)


class ViewOverlayPanelMixin:
    """Spectrum panel base"""

    @staticmethod
    def make_panel(parent, figsize, plot_id, axes_size=None):
        """Initialize plot panel"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotOverlay(plot_panel, figsize=figsize, axes_size=axes_size, plot_id=plot_id)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer


class ViewOverlay(ViewBase, ViewMPLMixin, ViewOverlayPanelMixin, ViewWaterfallMixin, ViewAxesMixin):
    """Viewer specialized in displaying overlay and comparison data"""

    VIEW_TYPE = "1d"
    DATA_KEYS = ("x", "y", "obj")
    MPL_KEYS = ["1d", "axes", "legend"]
    UPDATE_STYLES = ("line", "fill")
    ALLOWED_PLOTS = ("line", "multi-line", "waterfall")
    DEFAULT_PLOT = "line"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel(self.parent, self.figsize, self.PLOT_ID, self.axes_size)

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    def check_kwargs(self, **kwargs):
        self._x_label = kwargs.pop("x_label", self.x_label)
        self._y_label = kwargs.pop("y_label", self.y_label)
        return kwargs

    def check_input(self, *args, **kwargs):
        return args

    def plot_1d_overlay(self, x=None, y=None, array=None, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Overlay multiple line plots"""
        t_start = time.time()

        #         self.can_plot("waterfall")
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("waterfall")

        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        self.figure.clear()
        self.figure.plot_waterfall(
            x, y, array, x_label=self.y_label, y_label="Offset intensity", callbacks=self._callbacks, obj=obj, **kwargs
        )
        self.figure.repaint(repaint)

        # set data
        #         self._data.update(x=x, y=y, array=array, obj=obj)  # noqa
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_1d_compare(self, x_top, x_bottom, y_top, y_bottom, obj=None, labels=None, forced_kwargs=None, **kwargs):
        """Overlay two line plots"""
        t_start = time.time()
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        if labels is None:
            labels = ["", ""]
        kwargs.update(**CONFIG.get_mpl_parameters(["1d", "axes", "compare"]))  # self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)

        self.figure.clear()
        self.figure.plot_1d_compare(
            x_top,
            x_bottom,
            y_top,
            y_bottom,
            labels=labels,
            x_label=self.x_label,
            y_label=self.y_label,
            callbacks=self._callbacks,
            allow_extraction=self._allow_extraction,
            **kwargs,
        )
        self.figure.repaint()

        # # set data
        # self._data.update(
        #     x_top=x_top,
        #     x_bottom=x_bottom,
        #     y_top=y_top,
        #     y_bottom=y_bottom,
        #     obj_top=obj_top,
        #     obj_bottom=obj_bottom,
        #     labels=labels,
        # )
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_overlay(self, x, y, array_1, array_2, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Overlay heatmaps using masking"""
        t_start = time.time()
        #         self.can_plot("heatmap")
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))  # self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        # x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_2d_overlay(
            x,
            y,
            array_1,
            array_2,
            x_label=self.x_label,
            y_label=self.y_label,
            callbacks=self._callbacks,
            obj=obj,
            **kwargs,
        )
        self.figure.repaint(repaint)

        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_rgb(self, x, y, array, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Overlay multiple heatmaps using RGB overlay"""
        t_start = time.time()
        #         self.can_plot("heatmap")
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        # x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_2d_rgb(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        self.figure.repaint(repaint)

        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_heatmap(self, x, y, array, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Overlay heatmap plots : mean, stddev, variance"""
        t_start = time.time()
        #         self.can_plot("heatmap")
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        # x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_2d(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        self.figure.repaint(repaint)

        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_rmsd(self):
        """Overlay two heatmaps using RMSD plot"""

    def plot_2d_rmsf(self, x, y, array, y_top, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Overlay two heatmaps using RMSD + RMSF plot"""
        t_start = time.time()
        #         self.can_plot("heatmap")
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        self.figure.clear()
        self.figure.plot_heatmap_line(
            x, y, array, y_top, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        self.figure.repaint(repaint)

        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_grid_compare_rmsd(
        self, x, y, array_top, array_bottom, array, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs
    ):
        """Overlay two heatmaps using individual heatmaps -> RMSD plot"""
        t_start = time.time()
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        self.figure.clear()
        self.figure.plot_2d_grid_2_to_1(
            x,
            y,
            array_top,
            array_bottom,
            array,
            x_label=self.x_label,
            y_label=self.y_label,
            callbacks=self._callbacks,
            obj=obj,
            **kwargs,
        )
        self.figure.repaint(repaint)
        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_2d_rmsd_dot(self):
        """Generate RMSD dot plot from multiple heatmaps"""

    def plot_2d_rmsd_matrix(self):
        """Generate RMSD matrix plot from multiple heatmaps"""

    def plot_2d_grid_n_x_n(
        self, x, y, arrays, n_rows, n_cols, obj=None, repaint: bool = True, forced_kwargs=None, **kwargs
    ):
        """Overlay multiple heatmaps in a grid with linked zooming"""
        t_start = time.time()
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(["2d", "colorbar", "normalization", "axes"]))
        kwargs.update(**self.FORCED_KWARGS)
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        kwargs = self.check_kwargs(**kwargs)

        self.figure.clear()
        self.figure.plot_2d_grid_n_x_n(
            x,
            y,
            arrays,
            n_rows,
            n_cols,
            x_label=self.x_label,
            y_label=self.y_label,
            callbacks=self._callbacks,
            obj=obj,
            **kwargs,
        )
        self.figure.repaint(repaint)
        # set data
        # self._data.update(x=x, y=y, array=array, obj=obj)
        # self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def replot(self, **kwargs):
        pass

    def _update(self):
        pass

    def update_style(self, name: str):
        pass
