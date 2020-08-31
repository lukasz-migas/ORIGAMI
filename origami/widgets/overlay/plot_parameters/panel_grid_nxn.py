"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGridNxNSettings(PanelSettingsBase):
    """Violin settings"""

    # ui elements
    width_space_value, height_space_value = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        width_space_value = wx.StaticText(self, -1, "Width space:")
        self.width_space_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=2, initial=0, inc=0.25, size=(90, -1)
        )
        self.width_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.width_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        height_space_value = wx.StaticText(self, -1, "Height space:")
        self.height_space_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=2, initial=0, inc=0.25, size=(90, -1)
        )
        self.height_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.height_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(width_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_space_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(height_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.height_space_value, (n, 1), flag=wx.EXPAND)

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

        CONFIG.grid_nxn_width_space = self.width_space_value.GetValue()
        CONFIG.grid_nxn_height_space = self.height_space_value.GetValue()

        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.width_space_value.SetValue(CONFIG.grid_nxn_width_space)
        self.height_space_value.SetValue(CONFIG.grid_nxn_height_space)
        self.import_evt = False
