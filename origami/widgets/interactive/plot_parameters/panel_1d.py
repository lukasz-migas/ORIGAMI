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
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class Panel1dSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_line_width, bokeh_line_alpha, bokeh_line_style = None, None, None
    bokeh_line_color, bokeh_line_fill_under, bokeh_line_fill_alpha = None, None, None
    line_link_x, bokeh_bar_width, bokeh_bar_alpha = None, None, None
    bokeh_bar_edge_width, bokeh_bar_edge_same_as_fill, bokeh_bar_edge_color = None, None, None
    bokeh_scatter_marker, bokeh_scatter_size, bokeh_scatter_alpha = None, None, None
    bokeh_scatter_edge_width, bokeh_scatter_edge_same_as_fill, bokeh_scatter_edge_color = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        plot_line_width_value = make_static_text(self, "Line width:")
        self.bokeh_line_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50, -1))
        self.bokeh_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_transparency_value = make_static_text(self, "Line transparency:")
        self.bokeh_line_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_line_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_style_choice = make_static_text(self, "Line style:")
        self.bokeh_line_style = wx.ComboBox(self, -1, choices=CONFIG.bokeh_line_style_choices, style=wx.CB_READONLY)
        self.bokeh_line_style.Bind(wx.EVT_COMBOBOX, self.on_apply)

        bokeh_line_color_color_btn = make_static_text(self, "Line color:")
        self.bokeh_line_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="bokeh_line_color")
        self.bokeh_line_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot_line_fill_under = make_static_text(self, "Fill under line:")
        self.bokeh_line_fill_under = make_checkbox(self, "")
        self.bokeh_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_apply)

        plot_fill_transparency_value = make_static_text(self, "Fill transparency:")
        self.bokeh_line_fill_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_line_fill_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_link_x = make_static_text(self, "Hover linked to X-axis:")
        self.line_link_x = make_checkbox(self, "")
        self.line_link_x.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.line_link_x.SetToolTip(
            wx.ToolTip("Hover linked to the x-axis values. Can *significantly* slow plots with many data points!")
        )

        bar_width_value = make_static_text(self, "Bar width:")
        self.bokeh_bar_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.01, max=10, inc=0.25, size=(50, -1))
        self.bokeh_bar_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_transparency_value = make_static_text(self, "Bar transparency:")
        self.bokeh_bar_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_bar_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_line_width_value = make_static_text(self, "Edge width:")
        self.bokeh_bar_edge_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.25, size=(50, -1))
        self.bokeh_bar_edge_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_edge_same_as_fill = make_static_text(self, "Edge same as fill:")
        self.bokeh_bar_edge_same_as_fill = make_checkbox(self, "")
        self.bokeh_bar_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)

        bar_edge_color_btn = make_static_text(self, "Edge color:")
        self.bokeh_bar_edge_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="bokeh_bar_edge_color")
        self.bokeh_bar_edge_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        scatter_shape_choice = make_static_text(self, "Marker shape:")
        self.bokeh_scatter_marker = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_scatter_marker_choices, style=wx.CB_READONLY
        )
        self.bokeh_scatter_marker.Bind(wx.EVT_COMBOBOX, self.on_apply)

        scatter_size_value = make_static_text(self, "Marker size:")
        self.bokeh_scatter_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.5, max=100, inc=5, size=(50, -1))
        self.bokeh_scatter_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_transparency_value = make_static_text(self, "Marker transparency:")
        self.bokeh_scatter_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bokeh_scatter_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_line_width_value = make_static_text(self, "Edge width:")
        self.bokeh_scatter_edge_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.25, size=(50, -1))
        self.bokeh_scatter_edge_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_marker_edge_same_as_fill = make_static_text(self, "Edge same as fill:")
        self.bokeh_scatter_edge_same_as_fill = make_checkbox(self, "")
        self.bokeh_scatter_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)

        scatter_marker_edge_color_btn = make_static_text(self, "Edge color:")
        self.bokeh_scatter_edge_color = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="bokeh_scatter_edge_color"
        )
        self.bokeh_scatter_edge_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        line_parameters_label = wx.StaticText(self, -1, "Line parameters")
        set_item_font(line_parameters_label)

        marker_parameters_label = wx.StaticText(self, -1, "Marker parameters")
        set_item_font(marker_parameters_label)

        barplot_parameters_label = wx.StaticText(self, -1, "Barplot parameters")
        set_item_font(barplot_parameters_label)

        n_col, n_span = 2, 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(line_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_style_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_style, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bokeh_line_color_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_fill_under, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_fill_under, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot_fill_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_line_fill_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_link_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.line_link_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(marker_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_shape_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_marker, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_size_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_size, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_edge_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_marker_edge_same_as_fill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_edge_same_as_fill, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(scatter_marker_edge_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_scatter_edge_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(barplot_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_bar_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_bar_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_bar_edge_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_edge_same_as_fill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_bar_edge_same_as_fill, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(bar_edge_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_bar_edge_color, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, _ = self._on_assign_color(evt)

        # update configuration and button color
        if source == "bokeh_line_color":
            self.bokeh_line_color.SetBackgroundColour(color_255)
        elif source == "bokeh_bar_edge_color":
            self.bokeh_bar_edge_color.SetBackgroundColour(color_255)
        elif source == "bokeh_scatter_edge_color":
            self.bokeh_scatter_edge_color.SetBackgroundColour(color_255)

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
            # line
            "bokeh_line_width": self.bokeh_line_width.GetValue(),
            "bokeh_line_alpha": self.bokeh_line_alpha.GetValue(),
            "bokeh_line_style": self.bokeh_line_style.GetStringSelection(),
            "bokeh_line_fill_alpha": self.bokeh_line_fill_alpha.GetValue(),
            "bokeh_line_fill_under": self.bokeh_line_fill_under.GetValue(),
            "bokeh_line_color": convert_rgb_255_to_1(self.bokeh_line_color.GetBackgroundColour()),
            # scatter
            "bokeh_scatter_marker": self.bokeh_scatter_marker.GetStringSelection(),
            "bokeh_scatter_size": self.bokeh_scatter_size.GetValue(),
            "bokeh_scatter_alpha": self.bokeh_scatter_alpha.GetValue(),
            "bokeh_scatter_edge_width": self.bokeh_scatter_edge_width.GetValue(),
            "bokeh_scatter_edge_same_as_fill": self.bokeh_scatter_edge_same_as_fill.GetValue(),
            "bokeh_scatter_edge_color": convert_rgb_255_to_1(self.bokeh_scatter_edge_color.GetBackgroundColour()),
            # bar
            "bokeh_bar_width": self.bokeh_bar_width.GetValue(),
            "bokeh_bar_alpha": self.bokeh_bar_alpha.GetValue(),
            "bokeh_bar_edge_width": self.bokeh_bar_edge_width.GetValue(),
            "bokeh_bar_edge_same_as_fill": self.bokeh_bar_edge_same_as_fill.GetValue(),
            "bokeh_bar_edge_color": convert_rgb_255_to_1(self.bokeh_bar_edge_color.GetBackgroundColour()),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True

        # line parameters
        self.bokeh_line_width.SetValue(config.get("bokeh_line_width", CONFIG.bokeh_line_width))
        self.bokeh_line_alpha.SetValue(config.get("bokeh_line_alpha", CONFIG.bokeh_line_alpha))
        self.bokeh_line_style.SetStringSelection(config.get("bokeh_line_style", CONFIG.bokeh_line_style))
        self.bokeh_line_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_line_color", CONFIG.bokeh_line_color))
        )
        self.bokeh_line_fill_under.SetValue(config.get("bokeh_line_fill_under", CONFIG.bokeh_line_fill_under))
        self.bokeh_line_fill_alpha.SetValue(config.get("bokeh_line_fill_alpha", CONFIG.bokeh_line_fill_alpha))
        # self.line_link_x.SetValue(config.get("bokeh_line_fill_alpha", CONFIG.bokeh))

        # scatter parameters
        self.bokeh_scatter_marker.SetStringSelection(config.get("bokeh_scatter_marker", CONFIG.bokeh_scatter_marker))
        self.bokeh_scatter_size.SetValue(config.get("bokeh_scatter_size", CONFIG.bokeh_scatter_size))
        self.bokeh_scatter_alpha.SetValue(config.get("bokeh_scatter_alpha", CONFIG.bokeh_scatter_alpha))
        self.bokeh_scatter_edge_width.SetValue(config.get("bokeh_scatter_edge_width", CONFIG.bokeh_scatter_edge_width))
        self.bokeh_scatter_edge_same_as_fill.SetValue(
            config.get("bokeh_scatter_edge_same_as_fill", CONFIG.bokeh_scatter_edge_same_as_fill)
        )
        self.bokeh_scatter_edge_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_scatter_edge_color", CONFIG.bokeh_scatter_edge_color))
        )

        # bar parameters
        self.bokeh_bar_width.SetValue(config.get("bokeh_bar_width", CONFIG.bokeh_bar_width))
        self.bokeh_bar_alpha.SetValue(config.get("bokeh_bar_alpha", CONFIG.bokeh_bar_alpha))
        self.bokeh_bar_edge_width.SetValue(config.get("bokeh_bar_edge_width", CONFIG.bokeh_bar_edge_width))
        self.bokeh_bar_edge_same_as_fill.SetValue(
            config.get("bokeh_bar_edge_same_as_fill", CONFIG.bokeh_bar_edge_same_as_fill)
        )
        self.bokeh_bar_edge_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_bar_edge_color", CONFIG.bokeh_bar_edge_color))
        )
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
