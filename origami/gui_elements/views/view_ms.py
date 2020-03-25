# Local imports
# Third-party imports
# Third-party imports
import wx

from origami.visuals.mpl.plot_spectrum import PlotSpectrum


class ViewBase:
    def __init__(self, parent, figsize, config, title):
        self.parent = parent
        self.figsize = figsize
        self.config = config
        self.title = title
        self.x_label = None
        self.y_label = None

        self.document_name = None
        self.dataset_name = None

    def __repr__(self):
        return f"{self.__class__.__name__}<title={self.title}>"

    def set_document(self, **kwargs):
        """Set document information for particular plot"""
        if "document" in kwargs:
            self.document_name = kwargs["document"]
        if "dataset" in kwargs:
            self.document_name = kwargs["dataset"]

    def plot(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def update(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")


class ViewSpectrum(ViewBase):
    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotSpectrum(plot_panel, config=self.config, figsize=self.figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer


class ViewMassSpectrum(ViewSpectrum):
    def __init__(self, parent, figsize, config, title="MassSpectrum"):
        ViewSpectrum.__init__(self, parent, figsize, config, title)
        self.x_label = "m/z (Da)"
        self.y_label = "Intensity"
        self._panel, self._plot, self._sizer = self.make_panel()

    def plot(self, x, y, **kwargs):
        """Simple line plot"""
        self._plot.clear()
        self._plot.plot_1d(x, y, x_label=self.x_label, y_label=self.y_label, **kwargs)
        self._plot.repaint()

    def update(self, x, y, **kwargs):
        """Update plot without having to clear it"""
        self._plot.plot_1D_update_data(x, y, self.x_label, self.y_label, **kwargs)
