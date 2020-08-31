"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelRGBSettings(PanelSettingsBase):
    """Violin settings"""

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

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
