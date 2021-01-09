"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGridNxNSettings(PanelSettingsBase):
    """Violin settings"""

    # ui elements
    width_space_value, height_space_value, label_x_row, label_y_column = None, None, None, None
    ticks_each_row, ticks_each_column = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        width_space_value = wx.StaticText(self, -1, "Width space:")
        self.width_space_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=2, initial=0, inc=0.25, size=(90, -1)
        )
        self.width_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.width_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        height_space_value = wx.StaticText(self, -1, "Height space:")
        self.height_space_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=2, initial=0, inc=0.25, size=(90, -1)
        )
        self.height_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.height_space_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        label_x_row = wx.StaticText(self, -1, "Labels in bottom row (x)")
        self.label_x_row = make_checkbox(self, "", name="grid.nxn.axes")
        self.label_x_row.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.label_x_row.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        label_y_column = wx.StaticText(self, -1, "Labels in left column (y)")
        self.label_y_column = make_checkbox(self, "", name="grid.nxn.axes")
        self.label_y_column.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.label_y_column.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        ticks_each_row = wx.StaticText(self, -1, "Tick in each row (x)")
        self.ticks_each_row = make_checkbox(self, "", name="grid.nxn.axes")
        self.ticks_each_row.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ticks_each_row.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        ticks_each_column = wx.StaticText(self, -1, "Tick in each column (y)")
        self.ticks_each_column = make_checkbox(self, "", name="grid.nxn.axes")
        self.ticks_each_column.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ticks_each_column.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(width_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_space_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(height_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.height_space_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(label_x_row, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_x_row, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(label_y_column, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_y_column, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ticks_each_row, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ticks_each_row, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ticks_each_column, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ticks_each_column, (n, 1), flag=wx.EXPAND)

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
        CONFIG.grid_nxn_labels_x_first_row = self.label_x_row.GetValue()
        CONFIG.grid_nxn_labels_y_first_col = self.label_y_column.GetValue()
        CONFIG.grid_nxn_ticks_x_each = self.ticks_each_row.GetValue()
        CONFIG.grid_nxn_ticks_y_each = self.ticks_each_column.GetValue()
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.width_space_value.SetValue(CONFIG.grid_nxn_width_space)
        self.height_space_value.SetValue(CONFIG.grid_nxn_height_space)
        self.label_x_row.SetValue(CONFIG.grid_nxn_labels_x_first_row)
        self.label_y_column.SetValue(CONFIG.grid_nxn_labels_y_first_col)
        self.ticks_each_row.SetValue(CONFIG.grid_nxn_ticks_x_each)
        self.ticks_each_column.SetValue(CONFIG.grid_nxn_ticks_y_each)
        self.import_evt = False


def _main():

    from origami.app import App

    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelGridNxNSettings(self, None)

    app = App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
