"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class Panel1dSettings(PanelSettingsBase):
    """Violin settings"""

    plot1d_line_width_value, plot1d_line_color_btn, plot1d_line_style_value = None, None, None
    plot1d_underline_check, plot1d_underline_alpha_value, plot1d_underline_color_btn = None, None, None
    plot1d_marker_shape_value, plot1d_marker_size_value, plot1d_alpha_value = None, None, None
    plot1d_marker_color_btn, plot1d_marker_edge_color_check, plot1d_marker_edge_color_btn = None, None, None
    bar_width_value, bar_alpha_value, bar_line_width_value = None, None, None
    bar_color_edge_check, bar_edge_color_btn = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make 1d plot settings panel"""
        # line controls
        plot1d_line_width = wx.StaticText(self, -1, "Line width:")
        self.plot1d_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.lineWidth_1D),
            min=1,
            max=100,
            initial=CONFIG.lineWidth_1D,
            inc=1,
            size=(90, -1),
            name="1d.line.line.width",
        )
        self.plot1d_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot1d_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot1d_line_color = wx.StaticText(self, -1, "Line color:")
        self.plot1d_line_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="1d.line.line.color")
        self.plot1d_line_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.lineColour_1D))
        self.plot1d_line_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_line_style = wx.StaticText(self, -1, "Line style:")
        self.plot1d_line_style_value = wx.Choice(
            self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="1d.line.line.style"
        )
        self.plot1d_line_style_value.SetStringSelection(CONFIG.lineStyle_1D)
        self.plot1d_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot1d_line_style_value.Bind(wx.EVT_CHOICE, self.on_update)

        plot1d_underline = wx.StaticText(self, -1, "Fill under:")
        self.plot1d_underline_check = make_checkbox(self, "", name="1d.line.fill.show")
        self.plot1d_underline_check.SetValue(CONFIG.lineShadeUnder_1D)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot1d_underline_alpha = wx.StaticText(self, -1, "Fill transparency:")
        self.plot1d_underline_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.lineShadeUnderTransparency_1D),
            min=0,
            max=100,
            initial=CONFIG.lineShadeUnderTransparency_1D,
            inc=25,
            size=(90, -1),
            name="1d.line.fill.opacity",
        )
        self.plot1d_underline_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot1d_underline_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot1d_underline_color = wx.StaticText(self, -1, "Fill color:")
        self.plot1d_underline_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.line.fill.color"
        )
        self.plot1d_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.lineShadeUnderColour_1D))
        self.plot1d_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # markers controls
        plot1d_marker_shape = wx.StaticText(self, -1, "Marker shape:")
        self.plot1d_marker_shape_value = wx.Choice(self, -1, choices=list(CONFIG.markerShapeDict.keys()), size=(-1, -1))
        self.plot1d_marker_shape_value.SetStringSelection(CONFIG.markerShapeTXT_1D)
        self.plot1d_marker_shape_value.Bind(wx.EVT_CHOICE, self.on_apply)

        plot1d_marker_size = wx.StaticText(self, -1, "Marker size:")
        self.plot1d_marker_size_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.markerSize_1D), min=1, max=100, initial=1, inc=10, size=(90, -1)
        )
        self.plot1d_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot1d_alpha = wx.StaticText(self, -1, "Marker transparency:")
        self.plot1d_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.markerTransparency_1D),
            min=0,
            max=100,
            initial=CONFIG.markerTransparency_1D,
            inc=25,
            size=(90, -1),
        )
        self.plot1d_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot1d_marker_color = wx.StaticText(self, -1, "Marker fill color:")
        self.plot1d_marker_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.marker.fill"
        )
        self.plot1d_marker_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.markerColor_1D))
        self.plot1d_marker_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_marker_edge_color = wx.StaticText(self, -1, "Marker edge color:")
        self.plot1d_marker_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.marker.edge"
        )

        self.plot1d_marker_edge_color_check = make_checkbox(self, "Same as fill")
        self.plot1d_marker_edge_color_check.SetValue(CONFIG.markerEdgeUseSame_1D)
        self.plot1d_marker_edge_color_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot1d_marker_edge_color_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.plot1d_marker_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.markerEdgeColor_3D))
        self.plot1d_marker_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # bar plot controls
        bar_width_label = wx.StaticText(self, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.bar_width), min=0.01, max=10, inc=0.1, initial=CONFIG.bar_width, size=(90, -1)
        )
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_alpha_label = wx.StaticText(self, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.bar_alpha), min=0, max=1, initial=CONFIG.bar_alpha, inc=0.25, size=(90, -1)
        )
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_line_width_label = wx.StaticText(self, -1, "Bar edge line width:")
        self.bar_line_width_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.bar_lineWidth), min=0, max=5, initial=CONFIG.bar_lineWidth, inc=1, size=(90, -1)
        )
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_edge_color_label = wx.StaticText(self, -1, "Bar edge color:")
        self.bar_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.bar.edge"
        )
        self.bar_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.bar_edge_color))
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.bar_color_edge_check = make_checkbox(self, "Same as fill")
        self.bar_color_edge_check.SetValue(CONFIG.bar_sameAsFill)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        line_parameters_label = wx.StaticText(self, -1, "Line parameters")
        set_item_font(line_parameters_label)

        marker_parameters_label = wx.StaticText(self, -1, "Marker parameters")
        set_item_font(marker_parameters_label)

        barplot_parameters_label = wx.StaticText(self, -1, "Barplot parameters")
        set_item_font(barplot_parameters_label)

        n_col = 3
        n_span = 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(line_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_line_width_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_line_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot1d_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_line_style_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_underline, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_underline_check, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_underline_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_underline_alpha_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_underline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_underline_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)

        # marker settings
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(marker_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_marker_shape, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_marker_shape_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_marker_size_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_alpha_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_marker_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_marker_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot1d_marker_edge_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_marker_edge_color_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.plot1d_marker_edge_color_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)

        # barplot settings
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(barplot_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_width_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_alpha_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_line_width_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_edge_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_color_edge_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.bar_edge_color_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Update 1d parameters"""
        # plot 1D
        CONFIG.lineWidth_1D = str2num(self.plot1d_line_width_value.GetValue())
        CONFIG.lineStyle_1D = self.plot1d_line_style_value.GetStringSelection()
        CONFIG.markerSize_1D = str2num(self.plot1d_marker_size_value.GetValue())
        CONFIG.lineShadeUnder_1D = self.plot1d_underline_check.GetValue()
        CONFIG.lineShadeUnderTransparency_1D = str2num(self.plot1d_underline_alpha_value.GetValue())
        CONFIG.markerShapeTXT_1D = self.plot1d_marker_shape_value.GetStringSelection()
        CONFIG.markerShape_1D = CONFIG.markerShapeDict[self.plot1d_marker_shape_value.GetStringSelection()]
        CONFIG.markerTransparency_1D = str2num(self.plot1d_alpha_value.GetValue())

        # bar
        CONFIG.bar_width = self.bar_width_value.GetValue()
        CONFIG.bar_alpha = self.bar_alpha_value.GetValue()
        CONFIG.bar_sameAsFill = self.bar_color_edge_check.GetValue()
        CONFIG.bar_lineWidth = self.bar_line_width_value.GetValue()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update line controls"""
        self.plot1d_underline_alpha_value.Enable(self.plot1d_underline_check.GetValue())
        self.plot1d_underline_color_btn.Enable(self.plot1d_underline_check.GetValue())

        self.plot1d_marker_edge_color_btn.Enable(self.plot1d_marker_edge_color_check.GetValue())
        self.bar_edge_color_btn.Enable(self.bar_color_edge_check.GetValue())

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update 1d plots"""
        if evt is None:
            return
        source = evt.GetEventObject().GetName()
        if not source.startswith("1d.line"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source.split("1d.line.")[-1]

        try:
            view = self.panel_plot.get_view_from_name()
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "1d.marker.fill":
            CONFIG.markerColor_1D = color_1
            self.plot1d_marker_color_btn.SetBackgroundColour(color_255)
        elif source == "1d.marker.edge":
            CONFIG.markerEdgeColor_1D = color_1
            self.plot1d_marker_edge_color_btn.SetBackgroundColour(color_255)
        elif source == "1d.line.line.color":
            CONFIG.lineColour_1D = color_1
            self.plot1d_line_color_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "1d.line.fill.color":
            CONFIG.lineShadeUnderColour_1D = color_1
            self.plot1d_underline_color_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "1d.bar.edge":
            CONFIG.bar_edge_color = color_1
            self.bar_edge_color_btn.SetBackgroundColour(color_255)


class _TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
        self.scrolledPanel = Panel1dSettings(self, None)


def _main():

    app = wx.App()

    ex = _TestFrame()

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
