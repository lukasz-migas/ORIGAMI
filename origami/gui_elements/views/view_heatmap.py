# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D
from origami.gui_elements.views.view_base import ViewBase

LOGGER = logging.getLogger(__name__)


class ViewHeatmap(ViewBase):
    DATA_KEYS = ("array", "x", "y")
    MPL_KEYS = ["2D"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel, self.figure, self.sizer = self.make_panel()

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotHeatmap2D(plot_panel, figsize=self.figsize)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def check_input(self, x, y, array, obj):
        if x is None and y is None and array is None and obj is None:
            raise ValueError("You must provide the x/y/array values or container object")
        if x is None and y is None and array is None and obj is not None:
            x = obj.x
            y = obj.y
            array = obj.array
        return x, y, obj.array

    def plot(self, x=None, y=None, array=None, obj=None, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))

        try:
            self.update(x, y, array, obj, **kwargs)
        except AttributeError:
            x, y, array = self.check_input(x, y, array, obj)
            _ = kwargs.pop("x_label", "?")
            self.figure.clear()
            self.figure.plot_2d(
                x,
                y,
                array,
                x_label=self.x_label,
                y_label=self.y_label,
                callbacks=self._callbacks,
                allow_extraction=self._allow_extraction,
                **kwargs,
            )
            self.figure.repaint()

            # set data
            self._data.update(x=x, y=y)
            self._plt_kwargs = kwargs
            LOGGER.debug("Plotted data")

    def update(self, x=None, y=None, array=None, obj=None, **kwargs):
        """Update plot without having to clear it"""
        raise AttributeError("")

    #         self.set_document(obj, **kwargs)
    #         self.set_labels(obj, **kwargs)
    #
    #         # update plot
    #         x, y, array = self.check_input(x, y, array, obj)
    # #         self.figure.plot_1D_update_data(x, y, self.x_label, self.y_label, **kwargs)
    # #         self.figure.repaint()
    #
    #         # set data
    #         self._data.update(x=x, y=y)
    #         self._plt_kwargs = kwargs
    #         LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""

    def plot_violin(self):
        pass

    def plot_waterfall(self):
        pass

    def plot_joint(self):
        pass


class ViewIonHeatmap(ViewHeatmap):
    def __init__(self, parent, figsize, title="MassSpectrum", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Scans")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")


class ViewMassSpectrumHeatmap(ViewHeatmap):
    def __init__(self, parent, figsize, title="MassSpectrum", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Drift time (bins)")
