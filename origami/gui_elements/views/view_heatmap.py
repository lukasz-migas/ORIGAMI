"""View heatmap object"""
# Standard library imports
import logging
from copy import copy

# Third-party imports
import wx

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin

LOGGER = logging.getLogger(__name__)


class ViewHeatmap(ViewBase, ViewMPLMixin):
    """Viewer class for heatmap-based objects"""

    VIEW_TYPE = "2d"
    DATA_KEYS = ("array", "x", "y", "obj")
    MPL_KEYS = ["2d", "colorbar", "normalization"]
    NAME = get_short_hash()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel, self.figure, self.sizer = self.make_panel()

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotHeatmap2D(plot_panel, figsize=self.figsize, axes_size=self.axes_size, plot_id=self.NAME)

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
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
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
            self._plt_kwargs = kwargs
            LOGGER.debug("Plotted data")

    def update(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Update plot without having to clear it"""
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.plot_2d_update_data(x, y, array, self.x_label, self.y_label, obj=obj, **kwargs)
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""
        raise NotImplementedError("Must implement method")

    def plot_rgb(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""

    def plot_contour(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
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
        self._plt_kwargs = kwargs
        LOGGER.debug("Plotted data")

    def plot_violin(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a violin plot"""
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("violin")

        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs = self.check_kwargs(**kwargs)
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_violin(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Plotted data")

    def plot_waterfall(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("waterfall")

        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs = self.check_kwargs(**kwargs)
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_waterfall(
            x, y, array, x_label=self.y_label, y_label="Offset intensity", callbacks=self._callbacks, obj=obj, **kwargs
        )
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Plotted data")

    def plot_joint(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a joint-plot with top/side panels"""
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("joint")

        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
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
        self._plt_kwargs = kwargs
        LOGGER.debug("Plotted data")

    def update_style(self, name: str):
        """Update plot style"""
        if name.startswith("heatmap"):
            self.figure.plot_2d_update_heatmap_style(
                colormap=CONFIG.currentCmap,
                interpolation=CONFIG.interpolation,
                array=self._data["array"],
                cbar_kwargs=CONFIG.get_mpl_parameters("colorbar"),
            )
        elif name.startswith("normalization"):
            self.figure.plot_2d_update_normalization(
                array=self._data["array"], **CONFIG.get_mpl_parameters(["normalization"])
            )
        elif name.startswith("colorbar"):
            self.figure.plot_2d_update_colorbar(**CONFIG.get_mpl_parameters(["colorbar"]))
        elif name.startswith("contour"):
            print("Updating contour")
        elif name.startswith("joint"):
            print("Updating joint")
        elif name.startswith("waterfall"):
            # update data - requires full redraw
            if name.endswith(".data"):
                # get data and current state of the figure
                x, y, array, obj = self.get_data(["x", "y", "array", "obj"])
                #                 _limits = self.figure.get_xy_limits()
                self.plot_waterfall(x, y, array, obj, repaint=False)
            #                 self.figure.on_set_zoom_state(*_limits)
            else:
                self.figure.plot_waterfall_update(self._data["array"], name, **CONFIG.get_mpl_parameters(["waterfall"]))
        elif name.startswith("violin"):
            print("Updating violin")
        self.figure.repaint()
        LOGGER.debug(f"Updated plot styles - {name}")


class ViewIonHeatmap(ViewHeatmap):
    """Viewer class for extracted ions"""

    NAME = get_short_hash()

    def __init__(self, parent, figsize, title="IonHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Scans")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")


class ViewImagingIonHeatmap(ViewHeatmap):
    """Viewer class for extracted ions - LESA/Imaging documents"""

    NAME = get_short_hash()

    def __init__(self, parent, figsize, title="ImagingIonHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "x")
        self._y_label = kwargs.pop("y_label", "y")


class ViewMassSpectrumHeatmap(ViewHeatmap):
    """Viewer class for MS/DT heatmap"""

    NAME = get_short_hash()

    def __init__(self, parent, figsize, title="MassSpectrumHeatmap", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")
