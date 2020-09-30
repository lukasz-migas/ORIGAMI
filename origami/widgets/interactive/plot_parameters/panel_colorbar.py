"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

SC_SIZE = (75, -1)


class PanelColorbarSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    colorbar_colorbar, colorbar_modify_ticks, colorbar_precision, colorbar_use_scientific = None, None, None, None
    colorbar_edge_color, colorbar_edge_width, colorbar_label_fontsize = None, None, None
    colorbar_label_offset, colorbar_position, colorbar_offset_x, colorbar_offset_y = None, None, None, None
    colorbar_padding, colorbar_width, colorbar_label_fontweight = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        colorbar_colorbar = make_static_text(self, "Colorbar:")
        self.colorbar_colorbar = wx.CheckBox(self, -1, "", (15, 30))
        self.colorbar_colorbar.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.colorbar_colorbar.SetToolTip(wx.ToolTip("Add colorbar to the plot"))

        colorbar_modify_ticks = make_static_text(self, "Modify tick values:")
        self.colorbar_modify_ticks = wx.CheckBox(self, -1, "", (15, 30))
        self.colorbar_modify_ticks.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.colorbar_modify_ticks.SetToolTip(wx.ToolTip("Show ticks as percentage (0 - % - 100)"))

        colorbar_precision = make_static_text(self, "Precision:")
        self.colorbar_precision = wx.SpinCtrlDouble(self, min=0, max=5, inc=1, size=SC_SIZE)
        self.colorbar_precision.SetToolTip(wx.ToolTip("Number of decimal places in the colorbar tickers"))
        self.colorbar_precision.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.colorbar_use_scientific = wx.CheckBox(self, -1, "Scientific notation", (-1, -1))
        self.colorbar_use_scientific.SetToolTip(wx.ToolTip("Enable/disable scientific notation of colorbar tickers"))
        self.colorbar_use_scientific.Bind(wx.EVT_CHECKBOX, self.on_apply)

        colorbar_edge_color = make_static_text(self, "Edge color:")
        self.colorbar_edge_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="colorbar_edge_color")
        self.colorbar_edge_color.Bind(wx.EVT_BUTTON, self.on_apply)
        self.colorbar_edge_color.SetToolTip(wx.ToolTip("Color of the colorbar edge"))

        colorbar_edge_width = make_static_text(self, "Edge width:")
        self.colorbar_edge_width = wx.SpinCtrlDouble(self, inc=1.0, size=SC_SIZE, min=0, max=5)
        self.colorbar_edge_width.SetToolTip(wx.ToolTip("Width of the colorbar edge"))
        self.colorbar_edge_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_label_fontsize = make_static_text(self, "Label font size:")
        self.colorbar_label_fontsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=SC_SIZE)
        self.colorbar_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.colorbar_label_fontweight = make_checkbox(self, "bold")
        self.colorbar_label_fontweight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        colorbar_label_offset = make_static_text(self, "Label offset:")
        self.colorbar_label_offset = wx.SpinCtrlDouble(self, inc=1, size=SC_SIZE, min=0, max=100)
        self.colorbar_label_offset.SetToolTip(wx.ToolTip("Distance between the colorbar ticks and the labels"))
        self.colorbar_label_offset.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_position = make_static_text(self, "Position:")
        self.colorbar_position = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.interactive_colorbarPosition_choices
        )
        self.colorbar_position.SetToolTip(
            wx.ToolTip(
                "Colorbar position next to the plot. The colorbar orientation changes automatically. "
                + "If the value is set to 'above'/'below', you might want to set the position offset x/y to 0."
            )
        )
        self.colorbar_position.Bind(wx.EVT_COMBOBOX, self.on_apply)

        colorbar_offset_x = make_static_text(self, "Position offset X:")
        self.colorbar_offset_x = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.colorbar_offset_x.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the X axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.colorbar_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_offset_y = make_static_text(self, "Position offset Y:")
        self.colorbar_offset_y = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.colorbar_offset_y.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the Y axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.colorbar_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_padding = make_static_text(self, "Pad:")
        self.colorbar_padding = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.colorbar_padding.SetToolTip(wx.ToolTip(""))
        self.colorbar_padding.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colorbar_width = make_static_text(self, "Width:")
        self.colorbar_width = wx.SpinCtrlDouble(self, inc=5, size=SC_SIZE, min=0, max=100)
        self.colorbar_width.SetToolTip(wx.ToolTip("Width of the colorbar"))
        self.colorbar_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colorbar_colorbar, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_colorbar, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_modify_ticks, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_modify_ticks, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_precision, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_precision, (n, 1), flag=wx.EXPAND)
        grid.Add(self.colorbar_use_scientific, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_edge_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_edge_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_edge_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_edge_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.colorbar_label_fontweight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_offset, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_offset, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_offset_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_offset_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_offset_y, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_padding, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_padding, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_width, (n, 1), flag=wx.EXPAND)

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
                self.scrolledPanel = PanelColorbarSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
