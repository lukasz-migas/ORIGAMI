"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class Panel2dSettings(PanelSettingsBase):
    """General settings"""

    # ui elements

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

    def on_assign_color(self, evt):
        """Update color"""
        # get color

        # source, color_255, color_1 = self._on_assign_color(evt)

        # # update configuration and button color
        # if source == "1d.marker.fill":
        #     CONFIG.marker_fill_color = color_1
        #     self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

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
                self.scrolledPanel = Panel2dSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
