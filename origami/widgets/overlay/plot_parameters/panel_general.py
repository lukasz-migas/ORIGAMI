"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGeneralSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    plot2d_colormap_value, plot2d_colormap, plot2d_colormap, plot2d_colormap = None, None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        plot2d_colormap = wx.StaticText(self, -1, "Colormap:")
        self.plot2d_colormap_value = wx.Choice(
            self, -1, choices=CONFIG.colormap_choices, size=(-1, -1), name="2d.heatmap.heatmap"
        )
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_update_style)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot2d_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_colormap_value, (n, 1), flag=wx.EXPAND)

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
        CONFIG.heatmap_colormap = self.plot2d_colormap_value.GetStringSelection()
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.plot2d_colormap_value.SetStringSelection(CONFIG.heatmap_colormap)
        self.import_evt = False
