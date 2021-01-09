"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_toggle_btn
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


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
        self.legend_toggle = make_toggle_btn(self, "Off", wx.RED, name="legend.data")
        self.legend_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_controls)
        self.legend_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_update_style)

        legend_position = wx.StaticText(self, -1, "Position:")
        self.legend_position_value = wx.Choice(
            self, -1, choices=CONFIG.legend_position_choices, size=(-1, -1), name="legend.style"
        )
        self.legend_position_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.legend_position_value.Bind(wx.EVT_CHOICE, self.on_update_style)

        legend_columns = wx.StaticText(self, -1, "Columns:")
        self.legend_columns_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.legend_n_columns),
            min=1,
            max=5,
            initial=0,
            inc=1,
            size=(90, -1),
            name="legend.data",
        )
        self.legend_columns_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.legend_columns_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        legend_fontsize = wx.StaticText(self, -1, "Font size:")
        self.legend_fontsize_value = wx.Choice(
            self, -1, choices=CONFIG.legendFontChoice, size=(-1, -1), name="legend.style"
        )
        self.legend_fontsize_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.legend_fontsize_value.Bind(wx.EVT_CHOICE, self.on_update_style)

        legend_marker_size = wx.StaticText(self, -1, "Marker size:")
        self.legend_marker_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.legend_marker_size),
            min=0.5,
            max=5,
            initial=0,
            inc=0.5,
            size=(90, -1),
            name="legend.style",
        )
        self.legend_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.legend_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        legend_n_markers = wx.StaticText(self, -1, "Number of points:")
        self.legend_n_markers_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.legend_n_markers),
            min=1,
            max=10,
            initial=1,
            inc=1,
            size=(90, -1),
            name="legend.data",
        )
        self.legend_n_markers_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.legend_n_markers_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        legend_marker_before = wx.StaticText(self, -1, "Marker before label:")
        self.legend_marker_before_check = make_checkbox(self, "", name="legend.data")
        self.legend_marker_before_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.legend_marker_before_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        legend_alpha = wx.StaticText(self, -1, "Frame transparency:")
        self.legend_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.legend_transparency),
            min=0.0,
            max=1,
            initial=0,
            inc=0.05,
            size=(90, -1),
            name="legend.style",
        )
        self.legend_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.legend_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        legend_patch_alpha = wx.StaticText(self, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.legend_patch_transparency),
            min=0.0,
            max=1,
            initial=0,
            inc=0.25,
            size=(90, -1),
            name="legend.style",
        )
        self.legend_patch_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.legend_patch_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        legend_frame_label = wx.StaticText(self, -1, "Frame:")
        self.legend_frame_check = make_checkbox(self, "", name="legend.style")
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        legend_fancy = wx.StaticText(self, -1, "Rounded corners:")
        self.legend_fancybox_check = make_checkbox(self, "", name="legend.style")
        self.legend_fancybox_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.legend_fancybox_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

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
        if self.import_evt:
            return

        CONFIG.legend = self.legend_toggle.GetValue()
        CONFIG.legend_position = self.legend_position_value.GetStringSelection()
        CONFIG.legend_n_columns = str2int(self.legend_columns_value.GetValue())
        CONFIG.legend_font_size = self.legend_fontsize_value.GetStringSelection()
        CONFIG.legend_frame = self.legend_frame_check.GetValue()
        CONFIG.legend_transparency = str2num(self.legend_alpha_value.GetValue())
        CONFIG.legend_marker_size = str2num(self.legend_marker_size_value.GetValue())
        CONFIG.legend_n_markers = str2int(self.legend_n_markers_value.GetValue())
        CONFIG.legend_marker_first = self.legend_marker_before_check.GetValue()
        CONFIG.legend_patch_transparency = self.legend_patch_alpha_value.GetValue()
        CONFIG.legend_fancy_box = self.legend_fancybox_check.GetValue()

        self._parse_evt(evt)

    def on_update_style(self, evt):
        """Update"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("legend."):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source
        try:
            view = VIEW_REG.view
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
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

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.legend_toggle.SetValue(CONFIG.legend)
        self.legend_position_value.SetStringSelection(CONFIG.legend_position)
        self.legend_columns_value.SetValue(CONFIG.legend_n_columns)
        self.legend_marker_size_value.SetValue(CONFIG.legend_marker_size)
        self.legend_n_markers_value.SetValue(CONFIG.legend_n_markers)
        self.legend_marker_before_check.SetValue(CONFIG.legend_marker_first)
        self.legend_fontsize_value.SetStringSelection(CONFIG.legend_font_size)
        self.legend_alpha_value.SetValue(CONFIG.legend_transparency)
        self.legend_patch_alpha_value.SetValue(CONFIG.legend_patch_transparency)
        self.legend_frame_check.SetValue(CONFIG.legend_frame)
        self.legend_fancybox_check.SetValue(CONFIG.legend_fancy_box)
        self.import_evt = False


class _TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
        self.scrolledPanel = PanelLegendSettings(self, None)


def _main():

    from origami.app import App

    app = App()

    ex = _TestFrame()

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
