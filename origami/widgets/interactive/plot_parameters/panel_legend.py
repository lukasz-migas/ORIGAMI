"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelLegendSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_legend, bokeh_legend_location, bokeh_legend_orientation, bokeh_legend_font_size = None, None, None, None
    bokeh_legend_background_alpha, bokeh_legend_click_policy, bokeh_legend_mute_alpha = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        legend_legend = make_static_text(self, "Legend:")
        self.bokeh_legend = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_legend.Bind(wx.EVT_CHECKBOX, self.on_apply)

        legend_position = make_static_text(self, "Position:")
        self.bokeh_legend_location = wx.ComboBox(
            self, -1, style=wx.CB_READONLY, choices=CONFIG.bokeh_legend_location_choices
        )
        self.bokeh_legend_location.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_orientation = make_static_text(self, "Orientation:")
        self.bokeh_legend_orientation = wx.ComboBox(
            self, -1, style=wx.CB_READONLY, choices=CONFIG.bokeh_legend_orientation_choices
        )
        self.bokeh_legend_orientation.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_fontsize = make_static_text(self, "Font size:")
        self.bokeh_legend_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.bokeh_legend_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_transparency = make_static_text(self, "Legend transparency:")
        self.bokeh_legend_background_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_legend_background_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_click_policy = make_static_text(self, "Action:")
        self.bokeh_legend_click_policy = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_legend_click_policy_choices, style=wx.CB_READONLY
        )
        self.bokeh_legend_click_policy.Bind(wx.EVT_COMBOBOX, self.on_apply)

        legend_mute_transparency = make_static_text(self, "Line transparency:")
        self.bokeh_legend_mute_alpha = wx.SpinCtrlDouble(self, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_legend_mute_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(legend_legend, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(legend_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_location, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_orientation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_orientation, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_font_size, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_background_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_click_policy, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_click_policy, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_mute_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_legend_mute_alpha, (n, 1), flag=wx.EXPAND)

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
        return {
            "bokeh_legend": self.bokeh_legend.GetValue(),
            "bokeh_legend_click_policy": self.bokeh_legend_click_policy.GetValue(),
            "bokeh_legend_location": self.bokeh_legend_location.GetStringSelection(),
            "bokeh_legend_mute_alpha": self.bokeh_legend_mute_alpha.GetValue(),
            "bokeh_legend_background_alpha": self.bokeh_legend_background_alpha.GetValue(),
            "bokeh_legend_orientation": self.bokeh_legend_orientation.GetStringSelection(),
            "bokeh_legend_font_size": self.bokeh_legend_font_size.GetValue(),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_legend.SetValue(config.get("bokeh_legend", CONFIG.bokeh_legend))
        self.bokeh_legend_click_policy.SetStringSelection(
            config.get("bokeh_legend_click_policy", CONFIG.bokeh_legend_click_policy)
        )
        self.bokeh_legend_location.SetStringSelection(config.get("bokeh_legend_location", CONFIG.bokeh_legend_location))
        self.bokeh_legend_mute_alpha.SetValue(config.get("bokeh_legend_mute_alpha", CONFIG.bokeh_legend_mute_alpha))
        self.bokeh_legend_background_alpha.SetValue(
            config.get("bokeh_legend_background_alpha", CONFIG.bokeh_legend_background_alpha)
        )
        self.bokeh_legend_orientation.SetStringSelection(
            config.get("bokeh_legend_orientation", CONFIG.bokeh_legend_orientation)
        )
        self.bokeh_legend_font_size.SetValue(config.get("bokeh_legend_font_size", CONFIG.bokeh_legend_font_size))
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelLegendSettings(self, None)

        app = App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
