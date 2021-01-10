# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import MiniFrame
from origami.utils.time import ttime
from origami.utils.ranges import get_min_max
from origami.utils.screen import calculate_window_size
from origami.visuals.bkh_plots import PlotSpectrum

logger = logging.getLogger(__name__)

# Note: Sadly this does not work that well on Windows as Bokeh tools such as pan or zoom are not functional


class PanelPlotViewer(MiniFrame):
    """Interactive plot panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="Plot viewer...", style=wx.DEFAULT_FRAME_STYLE & ~(wx.MAXIMIZE_BOX))
        t_start = ttime()

        self.parent = parent
        self.presenter = presenter
        self.document_tree = self.parent.panelDocuments.documents
        self.panel_plot = self.parent.panelPlots

        # self.ionPanel = self.parent.panelMultipleIons
        # self.ionList = self.ionPanel.peaklist

        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling

        self._display_size = self.parent.GetSize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.7, 0.6])

        # pre-allocate parameters#
        self._recompute_peaks = True
        self._peaks_dict = None
        self._labels = None
        self._show_smoothed_spectrum = True
        self._mz_xrange = [None, None]
        self._mz_yrange = [None, None]
        self._n_peaks_max = 1000

        # setup kwargs
        self.document_title = kwargs.pop("document_title", None)
        self.dataset_type = kwargs.pop("dataset_type", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.mz_data = kwargs.pop("mz_data", None)

        # set title
        self.SetTitle(f"Plot viewer: {self.document_title} :: {self.dataset_type} :: {self.dataset_name}")

        # initialize gui
        self.make_gui()

        # initialize plot
        if self.mz_data is not None:
            self._mz_xrange = get_min_max(self.mz_data["xvals"])
            self._mz_yrange = get_min_max(self.mz_data["yvals"])
            self._mz_bin_width = self.data_processing.get_mz_spacing(self.mz_data["xvals"])
            self.plot.update_data(self.mz_data["xvals"], self.mz_data["yvals"])

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

        logger.info(f"Startup of peak picker took {ttime()-t_start:.2f} seconds")

    @property
    def mz_data(self):
        return self._mz_data

    @mz_data.setter
    def mz_data(self, value):
        self._mz_data = value
        self._mz_xrange = get_min_max(self.mz_data["xvals"])
        self._mz_yrange = get_min_max(self.mz_data["yvals"])

    def make_gui(self):
        """Make miniframe"""
        panel = wx.Panel(self, -1, size=(-1, -1), name="main")

        self.plot = PlotSpectrum(self, [], [], [], "Plot Spectrum")

        sizer_plot = wx.BoxSizer(wx.HORIZONTAL)
        sizer_plot.Add(self.plot.layout, 1, wx.EXPAND, 0)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(sizer_plot, 1, wx.EXPAND, 0)
        self.main_sizer.Fit(panel)

        self.SetSize(self._window_size)
        self.SetSizer(self.main_sizer)
        self.Layout()
        self.CentreOnScreen()
        self.SetFocus()
