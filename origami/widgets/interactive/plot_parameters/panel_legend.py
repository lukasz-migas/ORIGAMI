"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelLegendSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    legend_legend, legend_position, legend_orientation, legend_fontsize = None, None, None, None
    legend_transparency, legend_click_policy, legend_mute_transparency = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        legend_legend = make_static_text(self, "Legend:")
        self.legend_legend = wx.CheckBox(self, -1, "", (15, 30))
        self.legend_legend.Bind(wx.EVT_CHECKBOX, self.on_apply)

        legend_position = make_static_text(self, "Position:")
        self.legend_position = wx.ComboBox(self, -1, style=wx.CB_READONLY, choices=CONFIG.bokeh_legend_location_choices)
        self.legend_position.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_orientation = make_static_text(self, "Orientation:")
        self.legend_orientation = wx.ComboBox(
            self, -1, style=wx.CB_READONLY, choices=CONFIG.bokeh_legend_orientation_choices
        )
        self.legend_orientation.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_fontsize = make_static_text(self, "Font size:")
        self.legend_fontsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.legend_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_transparency = make_static_text(self, "Legend transparency:")
        self.legend_transparency = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.legend_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_click_policy = make_static_text(self, "Action:")
        self.legend_click_policy = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_legend_click_policy_choices, style=wx.CB_READONLY
        )
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_mute_transparency = make_static_text(self, "Line transparency:")
        self.legend_mute_transparency = wx.SpinCtrlDouble(self, min=0, max=1, inc=0.25, size=(50, -1))
        self.legend_mute_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(legend_legend, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_legend, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(legend_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_orientation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_orientation, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_fontsize, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_transparency, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_click_policy, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_click_policy, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_mute_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_mute_transparency, (n, 1), flag=wx.EXPAND)

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
                self.scrolledPanel = PanelLegendSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
