"""View heatmap object"""
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
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin
from origami.gui_elements.views.view_mixins import ViewAxesMixin
from origami.gui_elements.views.view_mixins import ViewViolinMixin
from origami.gui_elements.views.view_mixins import ViewWaterfallMixin

LOGGER = logging.getLogger(__name__)


class ViewHeatmap(ViewBase, ViewMPLMixin, ViewWaterfallMixin, ViewViolinMixin, ViewAxesMixin):
    """Viewer class for heatmap-based objects"""

    DATA_KEYS = ("array", "x", "y", "obj")
    MPL_KEYS = ["2d", "colorbar", "normalization", "axes"]
    UPDATE_STYLES = (
        "waterfall.line",
        "waterfall.line.color",
        "waterfall.fill",
        "waterfall.fill.color",
        "waterfall.label",
        "waterfall.label.reset",
        "waterfall.data",
        "violin.line",
        "violin.line.color",
        "violin.fill",
        "violin.fill.color",
        "violin.label",
        "violin.label.reset",
        "violin.data",
    )
    ALLOWED_PLOTS = ("heatmap", "contour", "joint", "waterfall", "violin", "rgb")
    DEFAULT_PLOT = "heatmap"
    VIEW_TYPE = "2d"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel()

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotHeatmap2D(plot_panel, figsize=self.figsize, axes_size=self.axes_size, plot_id=self.PLOT_ID)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    @staticmethod
    def check_input(x, y, array, obj):
        """Check user-input"""
        if x is None and y is None and array is None and obj is None:
            raise ValueError("You must provide the x/y/array values or container object")
        if x is None and y is None and array is None and obj is not None:
            x = obj.x
            y = obj.y
            array = obj.array
        return x, y, array

    def check_kwargs(self, **kwargs):
        """Check kwargs"""
        if "allow_extraction" not in kwargs:
            kwargs["allow_extraction"] = self._allow_extraction
        return kwargs

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple line plot"""
        t_start = time.time()
        self.can_plot("heatmap")
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)

        try:
            self.update(x, y, array, obj, repaint=repaint, **kwargs)
        except AttributeError:
            x, y, array = self.check_input(x, y, array, obj)
            self.figure.clear()
            self.figure.plot_2d(
                x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
            )
            if repaint:
                self.figure.repaint()

            # set data
            self._data.update(x=x, y=y, array=array, obj=obj)
            self.set_plot_parameters(**kwargs)
            LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def update(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Update plot without having to clear it"""
        t_start = time.time()
        self.can_plot("heatmap")
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.plot_2d_update_data(x, y, array, self.x_label, self.y_label, obj=obj, **kwargs)
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot data in {report_time(t_start)}")

    def replot(self, plot_type: str = None, repaint: bool = True, light_clear: bool = False):
        """Replot the current plot"""
        # get plot_type
        plot_type = self.get_plot_type(plot_type)

        if light_clear:
            self.light_clear()

        # get replot data
        array, x, y, obj = self.get_data(self.DATA_KEYS)
        if plot_type == "heatmap":
            self.plot(x, y, array, obj, repaint=repaint)
        if plot_type == "contour":
            self.plot_contour(x, y, array, obj, repaint=repaint)
        if plot_type == "joint":
            self.plot_joint(x, y, array, obj, repaint=repaint)
        if plot_type == "waterfall":
            self.plot_waterfall(x, y, array, obj, repaint=repaint)
        elif plot_type == "violin":
            self.plot_violin(x, y, array, obj, repaint=repaint)

    def plot_rgb(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):  # noqa
        """Plot object as a waterfall"""
        self.can_plot("rgb")

    def plot_contour(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""
        t_start = time.time()
        self.can_plot("contour")
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_2d_contour(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def plot_joint(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a joint-plot with top/side panels"""
        t_start = time.time()
        self.can_plot("joint")
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("joint")

        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_joint(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def update_style(self, name: str):
        """Update plot style"""
        t_start = time.time()

        # heatmap-specific updates
        kwargs = dict()
        if name.startswith("heatmap"):
            if not self.is_plotted_or_plot("heatmap", self.plot, self.DATA_KEYS):
                return

            if name.endswith("normalization"):
                kwargs = CONFIG.get_mpl_parameters(["normalization"])
                self.figure.plot_2d_update_normalization(array=self._data["array"], **kwargs)
            elif name.endswith("colorbar"):
                kwargs = CONFIG.get_mpl_parameters(["colorbar"])
                self.figure.plot_2d_update_colorbar(**kwargs)
            else:
                self.figure.plot_2d_update_heatmap_style(
                    colormap=CONFIG.heatmap_colormap,
                    interpolation=CONFIG.heatmap_interpolation,
                    array=self._data["array"],
                    cbar_kwargs=CONFIG.get_mpl_parameters("colorbar"),
                )
        # waterfall-specific updates
        elif name.startswith("waterfall"):
            kwargs = self._update_style_waterfall(name)
        # violin-specific updates
        elif name.startswith("violin"):
            kwargs = self._update_style_violin(name)
        elif name.startswith("axes"):
            kwargs = self._update_style_axes(name)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


class ViewIonHeatmap(ViewHeatmap):
    """Viewer class for extracted ions"""

    def __init__(self, parent, figsize, title="IonHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Scans")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")


class ViewImagingIonHeatmap(ViewHeatmap):
    """Viewer class for extracted ions - LESA/Imaging documents"""

    def __init__(self, parent, figsize, title="ImagingIonHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "x")
        self._y_label = kwargs.pop("y_label", "y")


class ViewMassSpectrumHeatmap(ViewHeatmap):
    """Viewer class for MS/DT heatmap"""

    PLOT_ID = get_short_hash()
    ALLOWED_PLOTS = ("heatmap", "contour", "joint")

    def __init__(self, parent, figsize, title="MassSpectrumHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")
