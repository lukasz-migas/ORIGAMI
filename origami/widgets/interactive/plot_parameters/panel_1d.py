"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class Panel1dSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    plot_line_width_value, plot_line_transparency_value, plot_line_style_choice = None, None, None
    plot_line_color_color_btn, plot_line_fill_under, plot_fill_transparency_value = None, None, None
    plot_line_link_x, bar_width_value, bar_transparency_value = None, None, None
    bar_line_width_value, bar_edge_same_as_fill, bar_edge_color_btn = None, None, None
    scatter_shape_choice, scatter_size_value, scatter_transparency_value = None, None, None
    scatter_line_width_value, scatter_marker_edge_same_as_fill, scatter_marker_edge_color_btn = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        plot_line_width_value = make_static_text(self, "Line width:")
        self.plot_line_width_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50, -1))
        self.plot_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_transparency_value = make_static_text(self, "Line transparency:")
        self.plot_line_transparency_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.plot_line_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_style_choice = make_static_text(self, "Line style:")
        self.plot_line_style_choice = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_line_style_choices, style=wx.CB_READONLY
        )
        self.plot_line_style_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        plot_line_color_color_btn = make_static_text(self, "Line color:")
        self.plot_line_color_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_line_color")
        self.plot_line_color_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot_line_fill_under = make_static_text(self, "Fill under line:")
        self.plot_line_fill_under = make_checkbox(self, "")
        self.plot_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_apply)

        plot_fill_transparency_value = make_static_text(self, "Fill transparency:")
        self.plot_fill_transparency_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.plot_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_line_link_x = make_static_text(self, "Hover linked to X-axis:")
        self.plot_line_link_x = make_checkbox(self, "")
        self.plot_line_link_x.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_line_link_x.SetToolTip(
            wx.ToolTip("Hover linked to the x-axis values. Can *significantly* slow plots with many data points!")
        )

        bar_width_value = make_static_text(self, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.01, max=10, inc=0.25, size=(50, -1))
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_transparency_value = make_static_text(self, "Bar transparency:")
        self.bar_transparency_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.bar_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_line_width_value = make_static_text(self, "Edge width:")
        self.bar_line_width_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.25, size=(50, -1))
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_edge_same_as_fill = make_static_text(self, "Edge same as fill:")
        self.bar_edge_same_as_fill = make_checkbox(self, "")
        self.bar_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)

        bar_edge_color_btn = make_static_text(self, "Edge color:")
        self.bar_edge_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_bar_edge_color")
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        scatter_shape_choice = make_static_text(self, "Marker shape:")
        self.scatter_shape_choice = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_scatter_marker_choices, style=wx.CB_READONLY
        )
        self.scatter_shape_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        scatter_size_value = make_static_text(self, "Marker size:")
        self.scatter_size_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.5, max=100, inc=5, size=(50, -1))
        self.scatter_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_transparency_value = make_static_text(self, "Marker transparency:")
        self.scatter_transparency_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.scatter_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_line_width_value = make_static_text(self, "Edge width:")
        self.scatter_line_width_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.25, size=(50, -1))
        self.scatter_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        scatter_marker_edge_same_as_fill = make_static_text(self, "Edge same as fill:")
        self.scatter_marker_edge_same_as_fill = make_checkbox(self, "")
        self.scatter_marker_edge_same_as_fill.Bind(wx.EVT_CHECKBOX, self.on_apply)

        scatter_marker_edge_color_btn = make_static_text(self, "Edge color:")
        self.scatter_marker_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_scatter_edge_color"
        )
        self.scatter_marker_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

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
        grid.Add(self.plot_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_line_transparency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_style_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_line_style_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_color_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_line_color_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_fill_under, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_line_fill_under, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot_fill_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_fill_transparency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_line_link_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_line_link_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(marker_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_shape_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_shape_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_size_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_size_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_transparency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_marker_edge_same_as_fill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_marker_edge_same_as_fill, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(scatter_marker_edge_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scatter_marker_edge_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(barplot_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_transparency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_edge_same_as_fill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_edge_same_as_fill, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(bar_edge_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_edge_color_btn, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # # update configuration and button color
        # if source == "1d.marker.fill":
        #     CONFIG.marker_fill_color = color_1
        #     self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

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
                self.scrolledPanel = Panel1dSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
