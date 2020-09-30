"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelPreprocessSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    preprocess_linearize_check, preprocess_linearize_binsize, preprocess_linearize_limit = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        preprocess_linearize_check = make_static_text(self, "Linearize:")
        self.preprocess_linearize_check = make_checkbox(self, "")
        self.preprocess_linearize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        preprocess_linearize_binsize = make_static_text(self, "Bin size:")
        self.preprocess_linearize_binsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.005, max=5, inc=0.1, size=(75, -1))
        self.preprocess_linearize_binsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        preprocess_linearize_limit = make_static_text(self, "Minimum size:")
        self.preprocess_linearize_limit = wx.SpinCtrlDouble(
            self, wx.ID_ANY, min=500, max=100000, inc=5000, size=(75, -1)
        )
        self.preprocess_linearize_limit.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(preprocess_linearize_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.preprocess_linearize_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(preprocess_linearize_binsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.preprocess_linearize_binsize, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(preprocess_linearize_limit, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.preprocess_linearize_limit, (n, 1), flag=wx.EXPAND)

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

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelPreprocessSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
