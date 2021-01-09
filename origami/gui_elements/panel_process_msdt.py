"""Heatmap pre-processing settings panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.mixins import DatasetMixin

logger = logging.getLogger(__name__)


class PanelProcessMSDT(MiniFrame, DatasetMixin):
    """Heatmap processing panel"""

    # panel settings
    TIMER_DELAY = 1000  # ms
    PANEL_BASE_TITLE = "MS/DT Extraction Parameters"

    # ui elements
    mz_min_value = None
    mz_max_value = None
    mz_bin_value = None
    cancel_btn = None

    def __init__(self, parent, presenter, update_widget: str = None, delay: int = 1000):
        MiniFrame.__init__(
            self,
            parent,
            title="MS/DT extraction parameters...",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        """Instantiate pre-processing module

        Parameters
        ----------
        parent :
            parent of the object
        presenter : ORIGAMI instance
            instance of the presenter/main class
        update_widget : str
            name of the pubsub event to be triggered when timer runs out
        delay : int
            amount of time between timed update
        """
        self.view = parent
        self.presenter = presenter

        # setup kwargs
        self.update_widget = update_widget
        self.TIMER_DELAY = delay

        # enable on-demand updates using wxTimer
        self._timer = None
        if self.update_widget:
            self._timer = wx.Timer(self, True)
            self.Bind(wx.EVT_TIMER, self.on_update_widget, self._timer)

        self.make_gui()
        self.setup()

        # setup layout
        self.CentreOnScreen()
        self.Show()
        self.SetFocus()

    def setup(self):
        """Setup UI"""
        self._dataset_mixin_setup()

    def on_close(self, evt, force: bool = False):
        """Overwrite close"""
        self._dataset_mixin_teardown()
        if self.update_widget:
            pub.sendMessage(self.update_widget)
        super(PanelProcessMSDT, self).on_close(evt, force)

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        mz_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z (min):")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_min_value.SetValue(str(CONFIG.msdt_panel_extract_mz_start))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_label = wx.StaticText(panel, wx.ID_ANY, "m/z (max): ")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_max_value.SetValue(str(CONFIG.msdt_panel_extract_mz_end))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_bin_label = wx.StaticText(panel, wx.ID_ANY, "m/z (bin size): ")
        self.mz_bin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_bin_value.SetValue(str(CONFIG.msdt_panel_extract_mz_bin_size))
        self.mz_bin_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Close", size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.cancel_btn)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(mz_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_max_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_bin_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_bin_value, (n, 1), flag=wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 5)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_apply(self, evt):
        """Update config values"""
        CONFIG.msdt_panel_extract_mz_start = str2num(self.mz_min_value.GetValue())
        CONFIG.msdt_panel_extract_mz_end = str2num(self.mz_max_value.GetValue())
        CONFIG.msdt_panel_extract_mz_bin_size = str2num(self.mz_bin_value.GetValue())

        if self.update_widget and isinstance(self.update_widget, str):
            self._timer.Stop()
            self._timer.StartOnce(self.TIMER_DELAY)

        if evt is not None:
            evt.Skip()

    def on_update_widget(self, _evt):
        """Timer-based update"""
        if self.update_widget and isinstance(self.update_widget, str) and not self._timer.IsRunning():
            pub.sendMessage(self.update_widget)


def _main():

    from origami.app import App

    app = App()
    ex = PanelProcessMSDT(None, None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
