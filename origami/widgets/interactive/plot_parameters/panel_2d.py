"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class Panel2dSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    heatmap_colormap = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        heatmap_colormap = make_static_text(self, "Colormap:")
        self.heatmap_colormap = wx.ComboBox(self, -1, choices=CONFIG.colormap_choices, style=wx.CB_READONLY)
        self.heatmap_colormap.Bind(wx.EVT_COMBOBOX, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(heatmap_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_colormap, (n, 1), flag=wx.EXPAND)

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

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {"bokeh_heatmap_colormap": self.heatmap_colormap.GetStringSelection()}

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.heatmap_colormap.SetStringSelection(config.get("bokeh_heatmap_colormap", CONFIG.bokeh_heatmap_colormap))
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = Panel2dSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
