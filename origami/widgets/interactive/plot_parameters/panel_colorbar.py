"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase

SC_SIZE = (75, -1)


class PanelColorbarSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_colorbar, bokeh_colorbar_modify_ticks, bokeh_colorbar_precision, bokeh_colorbar_use_scientific = (
        None,
        None,
        None,
        None,
    )
    bokeh_colorbar_edge_color, bokeh_colorbar_edge_width, bokeh_colorbar_label_font_size = None, None, None
    bokeh_colorbar_label_offset, bokeh_colorbar_location, bokeh_colorbar_offset_x, bokeh_colorbar_offset_y = (
        None,
        None,
        None,
        None,
    )
    bokeh_colorbar_padding, bokeh_colorbar_width, bokeh_colorbar_label_weight = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        colorbar_colorbar = make_static_text(self, "Colorbar:")
        self.bokeh_colorbar = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_colorbar.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_colorbar.SetToolTip(wx.ToolTip("Add colorbar to the plot"))

        colorbar_modify_ticks = make_static_text(self, "Modify tick values:")
        self.bokeh_colorbar_modify_ticks = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_colorbar_modify_ticks.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_colorbar_modify_ticks.SetToolTip(wx.ToolTip("Show ticks as percentage (0 - % - 100)"))

        colorbar_precision = make_static_text(self, "Precision:")
        self.bokeh_colorbar_precision = wx.SpinCtrlDouble(self, min=0, max=5, inc=1, size=SC_SIZE)
        self.bokeh_colorbar_precision.SetToolTip(wx.ToolTip("Number of decimal places in the colorbar tickers"))
        self.bokeh_colorbar_precision.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.bokeh_colorbar_use_scientific = wx.CheckBox(self, -1, "Scientific notation", (-1, -1))
        self.bokeh_colorbar_use_scientific.SetToolTip(
            wx.ToolTip("Enable/disable scientific notation of colorbar tickers")
        )
        self.bokeh_colorbar_use_scientific.Bind(wx.EVT_CHECKBOX, self.on_apply)

        colorbar_edge_color = make_static_text(self, "Edge color:")
        self.bokeh_colorbar_edge_color = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="colorbar_edge_color"
        )
        self.bokeh_colorbar_edge_color.Bind(wx.EVT_BUTTON, self.on_assign_color)
        self.bokeh_colorbar_edge_color.SetToolTip(wx.ToolTip("Color of the colorbar edge"))

        colorbar_edge_width = make_static_text(self, "Edge width:")
        self.bokeh_colorbar_edge_width = wx.SpinCtrlDouble(self, inc=1.0, size=SC_SIZE, min=0, max=5)
        self.bokeh_colorbar_edge_width.SetToolTip(wx.ToolTip("Width of the colorbar edge"))
        self.bokeh_colorbar_edge_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_label_fontsize = make_static_text(self, "Label font size:")
        self.bokeh_colorbar_label_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=SC_SIZE)
        self.bokeh_colorbar_label_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.bokeh_colorbar_label_weight = make_checkbox(self, "bold")
        self.bokeh_colorbar_label_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        colorbar_label_offset = make_static_text(self, "Label offset:")
        self.bokeh_colorbar_label_offset = wx.SpinCtrlDouble(self, inc=1, size=SC_SIZE, min=0, max=100)
        self.bokeh_colorbar_label_offset.SetToolTip(wx.ToolTip("Distance between the colorbar ticks and the labels"))
        self.bokeh_colorbar_label_offset.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_position = make_static_text(self, "Position:")
        self.bokeh_colorbar_location = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_colorbar_location_choices
        )
        self.bokeh_colorbar_location.SetToolTip(
            wx.ToolTip(
                "Colorbar position next to the plot. The colorbar orientation changes automatically. "
                + "If the value is set to 'above'/'below', you might want to set the position offset x/y to 0."
            )
        )
        self.bokeh_colorbar_location.Bind(wx.EVT_COMBOBOX, self.on_apply)

        colorbar_offset_x = make_static_text(self, "Position offset X:")
        self.bokeh_colorbar_offset_x = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.bokeh_colorbar_offset_x.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the X axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.bokeh_colorbar_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_offset_y = make_static_text(self, "Position offset Y:")
        self.bokeh_colorbar_offset_y = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.bokeh_colorbar_offset_y.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the Y axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.bokeh_colorbar_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_padding = make_static_text(self, "Pad:")
        self.bokeh_colorbar_padding = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.bokeh_colorbar_padding.SetToolTip(wx.ToolTip(""))
        self.bokeh_colorbar_padding.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_width = make_static_text(self, "Width:")
        self.bokeh_colorbar_width = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.bokeh_colorbar_width.SetToolTip(wx.ToolTip("Width of the colorbar"))
        self.bokeh_colorbar_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colorbar_colorbar, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_modify_ticks, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_modify_ticks, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_precision, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_precision, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_colorbar_use_scientific, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_edge_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_edge_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_edge_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_edge_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_label_font_size, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_colorbar_label_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_offset, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_label_offset, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_location, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_offset_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_offset_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_offset_y, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_padding, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_padding, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_colorbar_width, (n, 1), flag=wx.EXPAND)

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

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, _ = self._on_assign_color(evt)

        # update configuration and button color
        if source == "colorbar_edge_color":
            self.bokeh_colorbar_edge_color.SetBackgroundColour(color_255)

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {
            "bokeh_colorbar": self.bokeh_colorbar.GetValue(),
            "bokeh_colorbar_modify_ticks": self.bokeh_colorbar_modify_ticks.GetValue(),
            "bokeh_colorbar_precision": self.bokeh_colorbar_precision.GetValue(),
            "bokeh_colorbar_use_scientific": self.bokeh_colorbar_use_scientific.GetValue(),
            "bokeh_colorbar_edge_color": convert_rgb_255_to_1(self.bokeh_colorbar_edge_color.GetBackgroundColour()),
            "bokeh_colorbar_edge_width": self.bokeh_colorbar_edge_width.GetValue(),
            "bokeh_colorbar_label_font_size": self.bokeh_colorbar_label_font_size.GetValue(),
            "bokeh_colorbar_label_weight": self.bokeh_colorbar_label_weight.GetValue(),
            "bokeh_colorbar_label_offset": self.bokeh_colorbar_label_offset.GetValue(),
            "bokeh_colorbar_location": self.bokeh_colorbar_location.GetValue(),
            "bokeh_colorbar_offset_x": self.bokeh_colorbar_offset_x.GetValue(),
            "bokeh_colorbar_offset_y": self.bokeh_colorbar_offset_y.GetValue(),
            "bokeh_colorbar_padding": self.bokeh_colorbar_padding.GetValue(),
            "bokeh_colorbar_width": self.bokeh_colorbar_width.GetValue(),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_colorbar.SetValue(config.get("bokeh_colorbar", CONFIG.bokeh_colorbar))
        self.bokeh_colorbar_modify_ticks.SetValue(
            config.get("bokeh_colorbar_modify_ticks", CONFIG.bokeh_colorbar_modify_ticks)
        )
        self.bokeh_colorbar_precision.SetValue(config.get("bokeh_colorbar_precision", CONFIG.bokeh_colorbar_precision))
        self.bokeh_colorbar_edge_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_colorbar_edge_color", CONFIG.bokeh_colorbar_edge_color))
        )
        self.bokeh_colorbar_edge_width.SetValue(
            config.get("bokeh_colorbar_edge_width", CONFIG.bokeh_colorbar_edge_width)
        )
        self.bokeh_colorbar_edge_width.SetValue(
            config.get("bokeh_colorbar_edge_width", CONFIG.bokeh_colorbar_edge_width)
        )
        self.bokeh_colorbar_label_font_size.SetValue(
            config.get("bokeh_colorbar_label_font_size", CONFIG.bokeh_colorbar_label_font_size)
        )
        self.bokeh_colorbar_label_weight.SetValue(
            config.get("bokeh_colorbar_label_weight", CONFIG.bokeh_colorbar_label_weight)
        )
        self.bokeh_colorbar_label_offset.SetValue(
            config.get("bokeh_colorbar_label_offset", CONFIG.bokeh_colorbar_label_offset)
        )
        self.bokeh_colorbar_location.SetValue(config.get("bokeh_colorbar_location", CONFIG.bokeh_colorbar_location))
        self.bokeh_colorbar_offset_x.SetValue(config.get("bokeh_colorbar_offset_x", CONFIG.bokeh_colorbar_offset_x))
        self.bokeh_colorbar_offset_y.SetValue(config.get("bokeh_colorbar_offset_y", CONFIG.bokeh_colorbar_offset_y))
        self.bokeh_colorbar_padding.SetValue(config.get("bokeh_colorbar_padding", CONFIG.bokeh_colorbar_padding))
        self.bokeh_colorbar_width.SetValue(config.get("bokeh_colorbar_width", CONFIG.bokeh_colorbar_width))
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelColorbarSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
