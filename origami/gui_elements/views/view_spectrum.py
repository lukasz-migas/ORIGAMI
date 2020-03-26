# Third-party imports
import wx

# Local imports
from origami.gui_elements.views.view_base import ViewBase
from origami.visuals.mpl.plot_spectrum import PlotSpectrum


class ViewSpectrum(ViewBase):
    DATA_KEYS = ("x", "y")

    def __init__(self, *args):
        super().__init__(*args)
        self._panel, self._plot, self._sizer = self.make_panel()

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotSpectrum(plot_panel, config=self.config, figsize=self.figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)
        return plot_panel, plot_window, sizer

    def plot(self, x, y, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        self.set_document(**kwargs)
        try:
            self.update(x, y, **kwargs)
        except AttributeError:
            self._plot.clear()
            self._plot.plot_1d(x, y, _x_label=self.x_label, y_label=self.y_label, **kwargs)
            self._plot.repaint()

            # set data
            self._data.update(x=x, y=y)
            self._plt_kwargs = kwargs

    def update(self, x, y, **kwargs):
        """Update plot without having to clear it"""
        self.set_document(**kwargs)

        # update plot
        self._plot.plot_1D_update_data(x, y, self.x_label, self.y_label, **kwargs)

        # set data
        self._data.update(x=x, y=y)
        self._plt_kwargs = kwargs

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)


class ViewMassSpectrum(ViewSpectrum):
    def __init__(self, parent, figsize, config, title="MassSpectrum", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, config, title)
        self._x_label = kwargs.get("x_label", "m/z (Da)")
        self._y_label = kwargs.get("y_label", "Intensity")


class ViewChromatogram(ViewSpectrum):

    def __init__(self, parent, figsize, config, title="Chromatogram", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, config, title)
        self._x_label = kwargs.get("x_label", "Scans")
        self._y_label = kwargs.get("y_label", "Intensity")
