"""RGB panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelRGBSettings(PanelSettingsBase):
    """Violin settings"""

    adaptive_histogram_check, adaptive_histogram_n_bins, show_labels, adaptive_histogram_clip = None, None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        adaptive_histogram_check = wx.StaticText(self, -1, "Adaptive histogram:")
        self.adaptive_histogram_check = make_checkbox(self, "", name="rgb.data")
        self.adaptive_histogram_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.adaptive_histogram_check.Bind(wx.EVT_CHECKBOX, self.on_update_data)
        self.adaptive_histogram_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        adaptive_histogram_clip = wx.StaticText(self, -1, "No. bins:")
        self.adaptive_histogram_clip = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0.005, max=1, initial=0, inc=0.05, size=(90, -1), name="rgb.data"
        )
        self.adaptive_histogram_clip.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.adaptive_histogram_clip.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_data)

        adaptive_histogram_n_bins = wx.StaticText(self, -1, "No. bins:")
        self.adaptive_histogram_n_bins = wx.SpinCtrlDouble(
            self, -1, value=str(), min=64, max=1024, initial=0, inc=64, size=(90, -1), name="rgb.data"
        )
        self.adaptive_histogram_n_bins.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.adaptive_histogram_n_bins.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_data)

        show_labels = wx.StaticText(self, -1, "Show labels:")
        self.show_labels = make_checkbox(self, "", name="rgb.data")
        self.show_labels.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.show_labels.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(adaptive_histogram_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.adaptive_histogram_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(adaptive_histogram_clip, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.adaptive_histogram_clip, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(adaptive_histogram_n_bins, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.adaptive_histogram_n_bins, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(show_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.show_labels, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_update_style(self, evt):
        """Update waterfall plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return

        if not source.startswith("rgb."):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source
        try:
            view = VIEW_REG.view
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update controls"""
        CONFIG.rgb_adaptive_hist = self.adaptive_histogram_check.GetValue()
        self.adaptive_histogram_clip.Enable(CONFIG.rgb_adaptive_hist)
        self.adaptive_histogram_n_bins.Enable(CONFIG.rgb_adaptive_hist)

        self._parse_evt(evt)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return

        CONFIG.rgb_adaptive_hist = self.adaptive_histogram_check.GetValue()
        CONFIG.rgb_adaptive_hist_clip_limit = self.adaptive_histogram_clip.GetValue()
        CONFIG.rgb_adaptive_hist_n_bins = int(self.adaptive_histogram_n_bins.GetValue())
        CONFIG.rgb_show_labels = self.show_labels.GetValue()

        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.adaptive_histogram_check.SetValue(CONFIG.rgb_adaptive_hist)
        self.adaptive_histogram_clip.SetValue(CONFIG.rgb_adaptive_hist_clip_limit)
        self.adaptive_histogram_n_bins.SetValue(CONFIG.rgb_adaptive_hist_n_bins)
        self.show_labels.SetValue(CONFIG.rgb_show_labels)
        self.import_evt = False


def _main():
    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelRGBSettings(self, None)

    app = wx.App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
