"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class Panel1dSettings(PanelSettingsBase):
    """Violin settings"""

    spectrum_line_width, plot1d_line_color_btn, spectrum_line_style = None, None, None
    spectrum_line_fill_under, spectrum_fill_transparency, plot1d_underline_color_btn = None, None, None
    marker_shape, marker_size, marker_transparency = None, None, None
    plot1d_marker_color_btn, marker_edge_same_as_fill, plot1d_marker_edge_color_btn = None, None, None
    bar_width, bar_alpha, bar_line_width = None, None, None
    bar_edge_same_as_fill, bar_edge_color_btn = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make 1d plot settings panel"""
        # line controls
        plot1d_line_width = wx.StaticText(self, -1, "Line width:")
        self.spectrum_line_width = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.spectrum_line_width),
            min=1,
            max=100,
            initial=CONFIG.spectrum_line_width,
            inc=1,
            size=(90, -1),
            name="1d.line.line.width",
        )
        self.spectrum_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        plot1d_line_color = wx.StaticText(self, -1, "Line color:")
        self.plot1d_line_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="1d.line.line.color")
        self.plot1d_line_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_line_style = wx.StaticText(self, -1, "Line style:")
        self.spectrum_line_style = wx.Choice(
            self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="1d.line.line.style"
        )
        self.spectrum_line_style.Bind(wx.EVT_CHOICE, self.on_apply)
        self.spectrum_line_style.Bind(wx.EVT_CHOICE, self.on_update_style)

        plot1d_underline = wx.StaticText(self, -1, "Fill under:")
        self.spectrum_line_fill_under = make_checkbox(self, "", name="1d.line.fill.show")
        self.spectrum_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.spectrum_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.spectrum_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        plot1d_underline_alpha = wx.StaticText(self, -1, "Fill transparency:")
        self.spectrum_fill_transparency = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.spectrum_fill_transparency),
            min=0,
            max=1,
            initial=CONFIG.spectrum_fill_transparency,
            inc=0.25,
            size=(90, -1),
            name="1d.line.fill.opacity",
        )
        self.spectrum_fill_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_fill_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        plot1d_underline_color = wx.StaticText(self, -1, "Fill color:")
        self.plot1d_underline_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.line.fill.color"
        )
        self.plot1d_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # markers controls
        plot1d_marker_shape = wx.StaticText(self, -1, "Marker shape:")
        self.marker_shape = wx.Choice(self, -1, choices=CONFIG.marker_shape_choices, size=(-1, -1))
        self.marker_shape.Bind(wx.EVT_CHOICE, self.on_apply)

        plot1d_marker_size = wx.StaticText(self, -1, "Marker size:")
        self.marker_size = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.marker_size), min=1, max=100, initial=1, inc=10, size=(90, -1)
        )
        self.marker_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot1d_alpha = wx.StaticText(self, -1, "Marker transparency:")
        self.marker_transparency = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.marker_transparency),
            min=0,
            max=1,
            initial=CONFIG.marker_transparency,
            inc=0.25,
            size=(90, -1),
        )
        self.marker_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot1d_marker_color = wx.StaticText(self, -1, "Marker fill color:")
        self.plot1d_marker_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.marker.fill"
        )
        self.plot1d_marker_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.marker_edge_same_as_fill = make_checkbox(self, "Same as fill")
        self.marker_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.marker_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        plot1d_marker_edge_color = wx.StaticText(self, -1, "Marker edge color:")
        self.plot1d_marker_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.marker.edge"
        )
        self.plot1d_marker_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # bar plot controls
        bar_width_label = wx.StaticText(self, -1, "Bar width:")
        self.bar_width = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.bar_width), min=0.01, max=10, inc=0.1, initial=CONFIG.bar_width, size=(90, -1)
        )
        self.bar_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_alpha_label = wx.StaticText(self, -1, "Bar transparency:")
        self.bar_alpha = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.bar_alpha), min=0, max=1, initial=CONFIG.bar_alpha, inc=0.25, size=(90, -1)
        )
        self.bar_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_line_width_label = wx.StaticText(self, -1, "Bar edge line width:")
        self.bar_line_width = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.bar_line_width),
            min=0,
            max=5,
            initial=CONFIG.bar_line_width,
            inc=1,
            size=(90, -1),
        )
        self.bar_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_edge_color_label = wx.StaticText(self, -1, "Bar edge color:")
        self.bar_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="1d.bar.edge"
        )
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.bar_edge_same_as_fill = make_checkbox(self, "Same as fill")
        self.bar_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bar_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        line_parameters_label = wx.StaticText(self, -1, "Line parameters")
        set_item_font(line_parameters_label)

        marker_parameters_label = wx.StaticText(self, -1, "Marker parameters")
        set_item_font(marker_parameters_label)

        barplot_parameters_label = wx.StaticText(self, -1, "Barplot parameters")
        set_item_font(barplot_parameters_label)

        n_col, n_span = 3, 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(line_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.spectrum_line_width, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_line_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot1d_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.spectrum_line_style, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_underline, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.spectrum_line_fill_under, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_underline_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.spectrum_fill_transparency, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
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
        grid.Add(self.marker_shape, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.marker_size, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.marker_transparency, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot1d_marker_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot1d_marker_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot1d_marker_edge_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.marker_edge_same_as_fill, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
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
        grid.Add(self.bar_width, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_alpha, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_line_width, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_edge_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_edge_same_as_fill, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
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
        if self.import_evt:
            return
        # plot 1D
        CONFIG.spectrum_line_width = str2num(self.spectrum_line_width.GetValue())
        CONFIG.spectrum_line_style = self.spectrum_line_style.GetStringSelection()
        CONFIG.spectrum_line_fill_under = self.spectrum_line_fill_under.GetValue()
        CONFIG.spectrum_fill_transparency = str2num(self.spectrum_fill_transparency.GetValue())

        # markers
        CONFIG.marker_size = str2num(self.marker_size.GetValue())
        CONFIG.marker_edge_same_as_fill = self.marker_edge_same_as_fill.GetValue()
        CONFIG.marker_shape_txt = self.marker_shape.GetStringSelection()
        CONFIG.marker_shape = CONFIG.marker_shape_dict[self.marker_shape.GetStringSelection()]
        CONFIG.marker_transparency = str2num(self.marker_transparency.GetValue())

        # bar
        CONFIG.bar_edge_same_as_fill = self.bar_edge_same_as_fill.GetValue()
        CONFIG.bar_width = self.bar_width.GetValue()
        CONFIG.bar_alpha = self.bar_alpha.GetValue()
        CONFIG.bar_line_width = self.bar_line_width.GetValue()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update line controls"""
        self.spectrum_fill_transparency.Enable(self.spectrum_line_fill_under.GetValue())
        self.plot1d_underline_color_btn.Enable(self.spectrum_line_fill_under.GetValue())

        self.plot1d_marker_edge_color_btn.Enable(self.marker_edge_same_as_fill.GetValue())
        self.bar_edge_color_btn.Enable(self.bar_edge_same_as_fill.GetValue())

        self._parse_evt(evt)

    def on_update_style(self, evt):
        """Update 1d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("1d.line"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source.split("1d.line.")[-1]

        try:
            view = VIEW_REG.view
            view.update_style(name)
        except (AttributeError, KeyError):
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""
        # get color

        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "1d.marker.fill":
            CONFIG.marker_fill_color = color_1
            self.plot1d_marker_color_btn.SetBackgroundColour(color_255)
        elif source == "1d.marker.edge":
            CONFIG.marker_edge_color = color_1
            self.plot1d_marker_edge_color_btn.SetBackgroundColour(color_255)
        elif source == "1d.line.line.color":
            CONFIG.spectrum_line_color = color_1
            self.plot1d_line_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)
        elif source == "1d.line.fill.color":
            CONFIG.spectrum_fill_color = color_1
            self.plot1d_underline_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)
        elif source == "1d.bar.edge":
            CONFIG.bar_edge_color = color_1
            self.bar_edge_color_btn.SetBackgroundColour(color_255)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        # line
        self.spectrum_line_width.SetValue(CONFIG.spectrum_line_width)
        self.plot1d_line_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.spectrum_line_color))
        self.spectrum_line_style.SetStringSelection(CONFIG.spectrum_line_style)
        self.spectrum_line_fill_under.SetValue(CONFIG.spectrum_line_fill_under)
        self.spectrum_fill_transparency.SetValue(CONFIG.spectrum_fill_transparency)
        self.plot1d_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.spectrum_fill_color))

        # marker
        self.marker_shape.SetStringSelection(CONFIG.marker_shape_txt)
        self.marker_size.SetValue(CONFIG.marker_size)
        self.marker_transparency.SetValue(CONFIG.marker_transparency)
        self.plot1d_marker_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.marker_fill_color))
        self.marker_edge_same_as_fill.SetValue(CONFIG.marker_edge_same_as_fill)
        self.plot1d_marker_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.marker_edge_color))

        # bar
        self.bar_width.SetValue(CONFIG.bar_width)
        self.bar_alpha.SetValue(CONFIG.bar_alpha)
        self.bar_line_width.SetValue(CONFIG.bar_line_width)
        self.bar_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.bar_edge_color))
        self.bar_edge_same_as_fill.SetValue(CONFIG.bar_edge_same_as_fill)

        self.import_evt = False


if __name__ == "__main__":

    def _main():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = Panel1dSettings(self, None)

        app = App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
