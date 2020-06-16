# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.views.view_base import ViewBase

LOGGER = logging.getLogger(__name__)


class ViewSpectrum(ViewBase):
    """Viewer class for spectral data"""

    DATA_KEYS = ("x", "y")
    MPL_KEYS = ["1D"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel, self.figure, self.sizer = self.make_panel()

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotSpectrum(plot_panel, figsize=self.figsize)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    @staticmethod
    def check_input(x, y, obj):
        """Ensure that input is correct"""
        if x is None and y is None and obj is None:
            raise ValueError("You must provide the x/y values or container object")
        if x is None and y is None and obj is not None:
            x = obj.x
            y = obj.y
        return x, y

    def plot(self, x=None, y=None, obj=None, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))

        try:
            self.update(x, y, obj, **kwargs)
        except AttributeError:
            x, y = self.check_input(x, y, obj)
            self.figure.clear()
            self.figure.plot_1d(
                x,
                y,
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

    def update(self, x=None, y=None, obj=None, **kwargs):
        """Update plot without having to clear it"""
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y = self.check_input(x, y, obj)
        self.figure.plot_1D_update_data(x, y, self.x_label, self.y_label, **kwargs)
        self.figure.repaint()

        # set data
        self._data.update(x=x, y=y)
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""
        if kwargs is None:
            kwargs = self._plt_kwargs

        self.update(self._data["x"], self._data["y"], **kwargs)

    def smooth(self, **kwargs):
        """Performs basic smoothing"""
        pass


class ViewMassSpectrum(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="MassSpectrum", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewCompareMassSpectra(ViewMassSpectrum):
    """Specialized viewer for comparison of mass spectral data"""

    def __init__(self, parent, figsize, title="CompareMassSpectra", **kwargs):
        ViewMassSpectrum.__init__(self, parent, figsize, title=title, **kwargs)

    def plot(
        self, x_top=None, x_bottom=None, y_top=None, y_bottom=None, obj_top=None, obj_bottom=None, labels=None, **kwargs
    ):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        # self.set_document(obj, **kwargs)
        # self.set_labels(obj, **kwargs)

        if labels is None:
            labels = ["", ""]
        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))

        try:
            self.update(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom, labels, **kwargs)
        except AttributeError:
            # x, y = self.check_input(x, y, obj)
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

            # set data
            self._data.update(x=[x_top, x_bottom], y=[y_top, y_bottom])
            self._plt_kwargs = kwargs
            LOGGER.debug("Plotted data")

    def update(
        self, x_top=None, x_bottom=None, y_top=None, y_bottom=None, obj_top=None, obj_bottom=None, labels=None, **kwargs
    ):
        """Update plot without having to clear it"""
        # self.set_document(obj, **kwargs)
        # self.set_labels(obj, **kwargs)
        if labels is None:
            labels = ["", ""]
        # update plot
        # x, y = self.check_input(x, y, obj)
        self.figure.plot_1d_compare_update_data(x_top, x_bottom, y_top, y_bottom, labels, **kwargs)
        self.figure.repaint()

        # set data
        self._data.update(x=[x_top, x_bottom], y=[y_top, y_bottom])
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def update_style(self, *args, **kwargs):
        """Update plot style"""
        self.figure.plot_1D_update_style_by_label(*args, **kwargs)
        self.figure.repaint()


class ViewChromatogram(ViewSpectrum):
    """Specialized viewer for chromatographic data"""

    def __init__(self, parent, figsize, title="Chromatogram", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Scans")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewMobilogram(ViewSpectrum):
    """Specialized viewer for mobilogram data"""

    def __init__(self, parent, figsize, title="Mobilogram", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Drift time (bins)")
        self._y_label = kwargs.pop("y_label", "Intensity")
