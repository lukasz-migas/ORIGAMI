"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelWaterfallSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    waterfall_yaxis_increment, waterfall_fill_under, waterfall_fill_transparency = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        waterfall_yaxis_increment = make_static_text(self, "Y-axis increment:")
        self.waterfall_yaxis_increment = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.25, min=0, max=10, size=(50, -1))
        self.waterfall_yaxis_increment.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        waterfall_fill_under = make_static_text(self, "Shade under line:")
        self.waterfall_fill_under = make_checkbox(self, "")
        self.waterfall_fill_under.Bind(wx.EVT_CHECKBOX, self.on_apply)

        waterfall_fill_transparency = make_static_text(self, "Shade transparency:")
        self.waterfall_fill_transparency = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.25, min=0, max=1, size=(50, -1))
        self.waterfall_fill_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(waterfall_yaxis_increment, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_yaxis_increment, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_fill_under, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_fill_under, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_fill_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_fill_transparency, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return
        self._parse_evt(evt)

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":

    def _main():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelWaterfallSettings(self, None)

        app = App()
        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
