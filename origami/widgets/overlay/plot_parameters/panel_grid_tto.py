"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGridTTOSettings(PanelSettingsBase):
    """Grid (2->1) settings"""

    # ui elements
    width_space_value, height_space_value, n_rows_value, n_cols_value = None, None, None, None
    main_plot_proportion_value = None

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

        n_rows_value = wx.StaticText(self, -1, "No. rows:")
        self.n_rows_value = wx.SpinCtrl(self, -1, value=str(), min=2, max=10, initial=0, size=(90, -1))
        self.n_rows_value.Bind(wx.EVT_SPINCTRL, self.on_apply)
        self.n_rows_value.Bind(wx.EVT_SPINCTRL, self.on_update_style)

        n_cols_value = wx.StaticText(self, -1, "No. columns:")
        self.n_cols_value = wx.SpinCtrl(self, -1, value=str(), min=4, max=10, initial=0, size=(90, -1))
        self.n_cols_value.Bind(wx.EVT_SPINCTRL, self.on_apply)
        self.n_cols_value.Bind(wx.EVT_SPINCTRL, self.on_update_style)

        main_plot_proportion_value = wx.StaticText(self, -1, "Proportion (main):")
        self.main_plot_proportion_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=1, inc=0.2, initial=0, size=(90, -1)
        )
        self.main_plot_proportion_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.main_plot_proportion_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)
        set_tooltip(
            self.main_plot_proportion_value,
            "Proportion of the `no. columns` used to show the main plot. Values are always rounded and the side plot"
            " must contain at least columns",
        )

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(width_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_space_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(height_space_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.height_space_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(n_rows_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.n_rows_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(n_cols_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.n_cols_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(main_plot_proportion_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.main_plot_proportion_value, (n, 1), flag=wx.ALIGN_LEFT)

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

        CONFIG.grid_tto_width_space = self.width_space_value.GetValue()
        CONFIG.grid_tto_height_space = self.height_space_value.GetValue()
        CONFIG.grid_tto_n_rows = self.n_rows_value.GetValue()
        CONFIG.grid_tto_n_cols = self.n_cols_value.GetValue()
        CONFIG.grid_tto_main_x_proportion = self.main_plot_proportion_value.GetValue()

        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.width_space_value.SetValue(CONFIG.grid_tto_width_space)
        self.height_space_value.SetValue(CONFIG.grid_tto_height_space)
        self.n_rows_value.SetValue(CONFIG.grid_tto_n_rows)
        self.n_cols_value.SetValue(CONFIG.grid_tto_n_cols)
        self.main_plot_proportion_value.SetValue(CONFIG.grid_tto_main_x_proportion)
        self.import_evt = False


def _main():

    from origami.app import App

    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelGridTTOSettings(self, None)

    app = App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
