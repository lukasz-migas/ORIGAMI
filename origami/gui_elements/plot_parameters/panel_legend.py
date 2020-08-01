"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.styles import make_checkbox
from origami.styles import make_toggle_btn
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelLegendSettings(PanelSettingsBase):
    """Legend settings"""

    legend_toggle, legend_position_value, legend_columns_value = None, None, None
    legend_fontsize_value, legend_frame_check, legend_alpha_value = None, None, None
    legend_marker_size_value, legend_n_markers_value, legend_marker_before_check = None, None, None
    legend_fancybox_check, legend_patch_alpha_value = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make UI"""
        legend_toggle = wx.StaticText(self, -1, "Legend:")
        self.legend_toggle = make_toggle_btn(self, "Off", wx.RED)
        self.legend_toggle.SetValue(CONFIG.legend)
        self.legend_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_controls)

        legend_position = wx.StaticText(self, -1, "Position:")
        self.legend_position_value = wx.Choice(self, -1, choices=CONFIG.legendPositionChoice, size=(-1, -1))
        self.legend_position_value.SetStringSelection(CONFIG.legendPosition)
        self.legend_position_value.Bind(wx.EVT_CHOICE, self.on_apply)

        legend_columns = wx.StaticText(self, -1, "Columns:")
        self.legend_columns_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.legendColumns), min=1, max=5, initial=0, inc=1, size=(90, -1)
        )
        self.legend_columns_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_fontsize = wx.StaticText(self, -1, "Font size:")
        self.legend_fontsize_value = wx.Choice(self, -1, choices=CONFIG.legendFontChoice, size=(-1, -1))
        self.legend_fontsize_value.SetStringSelection(CONFIG.legendFontSize)
        self.legend_fontsize_value.Bind(wx.EVT_CHOICE, self.on_apply)

        legend_marker_size = wx.StaticText(self, -1, "Marker size:")
        self.legend_marker_size_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.legendMarkerSize), min=0.5, max=5, initial=0, inc=0.5, size=(90, -1)
        )
        self.legend_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_n_markers = wx.StaticText(self, -1, "Number of points:")
        self.legend_n_markers_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.legendNumberMarkers), min=1, max=10, initial=1, inc=1, size=(90, -1)
        )
        self.legend_n_markers_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_marker_before = wx.StaticText(self, -1, "Marker before label:")
        self.legend_marker_before_check = make_checkbox(self, "")
        self.legend_marker_before_check.SetValue(CONFIG.legendMarkerFirst)
        self.legend_marker_before_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        legend_alpha = wx.StaticText(self, -1, "Frame transparency:")
        self.legend_alpha_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.legendAlpha), min=0.0, max=1, initial=0, inc=0.05, size=(90, -1)
        )
        self.legend_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_patch_alpha = wx.StaticText(self, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.legendPatchAlpha), min=0.0, max=1, initial=0, inc=0.25, size=(90, -1)
        )
        self.legend_patch_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        legend_frame_label = wx.StaticText(self, -1, "Frame:")
        self.legend_frame_check = make_checkbox(self, "")
        self.legend_frame_check.SetValue(CONFIG.legendFrame)
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        legend_fancy = wx.StaticText(self, -1, "Rounded corners:")
        self.legend_fancybox_check = make_checkbox(self, "")
        self.legend_fancybox_check.SetValue(CONFIG.legendFancyBox)
        self.legend_fancybox_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(legend_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_toggle, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_columns, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_columns_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_fontsize_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_marker_size_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_n_markers, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_n_markers_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_marker_before, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_marker_before_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_patch_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_patch_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_frame_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_frame_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fancy, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_fancybox_check, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply legend parameters"""
        CONFIG.legend = self.legend_toggle.GetValue()
        CONFIG.legendPosition = self.legend_position_value.GetStringSelection()
        CONFIG.legendColumns = str2int(self.legend_columns_value.GetValue())
        CONFIG.legendFontSize = self.legend_fontsize_value.GetStringSelection()
        CONFIG.legendFrame = self.legend_frame_check.GetValue()
        CONFIG.legendAlpha = str2num(self.legend_alpha_value.GetValue())
        CONFIG.legendMarkerSize = str2num(self.legend_marker_size_value.GetValue())
        CONFIG.legendNumberMarkers = str2int(self.legend_n_markers_value.GetValue())
        CONFIG.legendMarkerFirst = self.legend_marker_before_check.GetValue()
        CONFIG.legendPatchAlpha = self.legend_patch_alpha_value.GetValue()
        CONFIG.legendFancyBox = self.legend_fancybox_check.GetValue()

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update plot data"""
        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update legend controls"""
        CONFIG.legend = self.legend_toggle.GetValue()
        self.legend_toggle.SetLabel("On" if CONFIG.legend else "Off")
        self.legend_toggle.SetForegroundColour(wx.WHITE)
        self.legend_toggle.SetBackgroundColour(wx.BLUE if CONFIG.legend else wx.RED)

        self.legend_position_value.Enable(CONFIG.legend)
        self.legend_columns_value.Enable(CONFIG.legend)
        self.legend_fontsize_value.Enable(CONFIG.legend)
        self.legend_frame_check.Enable(CONFIG.legend)
        self.legend_alpha_value.Enable(CONFIG.legend)
        self.legend_marker_size_value.Enable(CONFIG.legend)
        self.legend_n_markers_value.Enable(CONFIG.legend)
        self.legend_marker_before_check.Enable(CONFIG.legend)
        self.legend_fancybox_check.Enable(CONFIG.legend)
        self.legend_patch_alpha_value.Enable(CONFIG.legend)

        self._parse_evt(evt)


class _TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
        self.scrolledPanel = PanelLegendSettings(self, None)


def _main():

    app = wx.App()

    ex = _TestFrame()

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
