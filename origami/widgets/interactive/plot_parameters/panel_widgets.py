"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelWidgetsSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    widgets_position, widgets_add_widgets, widgets_check_all_widgets, widgets_general_zoom_1d = None, None, None, None
    widgets_general_hover_mode, widgets_general_figure_width, widgets_legend_all = None, None, None
    widgets_general_figure_height, widgets_color_colorblind, widgets_annotations_all = None, None, None
    widgets_color_colormap, widgets_annotations_offset_y, widgets_legend_show = None, None, None
    widgets_annotations_show, widgets_annotations_font_size, widgets_legend_transparency = None, None, None
    widgets_annotations_rotate, widgets_annotations_offset_x, widgets_legend_orientation = None, None, None
    widgets_legend_position, widgets_scatter_all, widgets_scatter_size = None, None, None
    widgets_scatter_transparency = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        widgets_position = make_static_text(self, "Widget position:")
        self.widgets_position = wx.ComboBox(self, -1, style=wx.CB_READONLY, choices=["right", "left", "top", "bottom"])
        self.widgets_position.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.widgets_add_widgets = make_checkbox(self, "Add custom JS widgets")
        self.widgets_add_widgets.Bind(wx.EVT_CHECKBOX, self.on_add_custom_widgets)

        self.widgets_check_all_widgets = make_checkbox(self, "Check/uncheck all")
        self.widgets_check_all_widgets.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        # general
        general_label = wx.StaticText(self, -1, "General widgets")
        set_item_font(general_label)

        self.widgets_general_zoom_1d = make_checkbox(self, "Y-axis scale slider")
        self.widgets_general_zoom_1d.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_general_hover_mode = make_checkbox(self, "Hover mode toggle", name="hover_mode")
        self.widgets_general_hover_mode.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_general_figure_width = make_checkbox(self, "Figure width", name="figure_width")
        self.widgets_general_figure_width.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_general_figure_height = make_checkbox(self, "Figure height", name="figure_height")
        self.widgets_general_figure_height.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # color
        color_label = wx.StaticText(self, -1, "Color widgets")
        set_item_font(color_label)

        self.widgets_color_colorblind = make_checkbox(self, "Colorblind toggle")
        self.widgets_color_colorblind.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_color_colormap = make_checkbox(self, "Colormap dropdown")
        self.widgets_color_colormap.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # labels
        annotations_label = wx.StaticText(self, -1, "Label and annotation widgets")
        set_item_font(annotations_label)

        self.widgets_annotations_all = make_checkbox(self, "All/None annotation widgets")
        self.widgets_annotations_all.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_annotations_show = make_checkbox(self, "Show/hide toggle", name="annotations_toggle")
        self.widgets_annotations_show.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_annotations_font_size = make_checkbox(self, "Font size slider", name="annotations_font_size")
        self.widgets_annotations_font_size.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_annotations_rotate = make_checkbox(self, "Rotation slider", name="annotations_rotation")
        self.widgets_annotations_rotate.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_annotations_offset_x = make_checkbox(self, "Horizontal offset slider", name="annotations_offset_x")
        self.widgets_annotations_offset_x.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_annotations_offset_y = make_checkbox(self, "Vertical offset slider", name="annotations_offset_y")
        self.widgets_annotations_offset_y.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # labels
        legend_label = wx.StaticText(self, -1, "Legend widgets")
        set_item_font(legend_label)

        self.widgets_legend_all = make_checkbox(self, "All/None legend widgets")
        self.widgets_legend_all.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_legend_show = make_checkbox(self, "Show/hide toggle", name="legend_name")
        self.widgets_legend_show.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_legend_transparency = make_checkbox(self, "Legend transparency", name="legend_transparency")
        self.widgets_legend_transparency.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_legend_orientation = make_checkbox(self, "Legend rotation", name="legend_orientation")
        self.widgets_legend_orientation.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_legend_position = make_checkbox(self, "Legend position", name="legend_position")
        self.widgets_legend_position.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # scatter
        scatter_label = wx.StaticText(self, -1, "Scatter widgets")
        set_item_font(scatter_label)

        self.widgets_scatter_all = make_checkbox(self, "All/None scatter widgets")
        self.widgets_scatter_all.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_scatter_size = make_checkbox(self, "Size slider", name="scatter_size")
        self.widgets_scatter_size.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.widgets_scatter_transparency = make_checkbox(self, "Transparency slider", name="scatter_transparency")
        self.widgets_scatter_transparency.Bind(wx.EVT_CHECKBOX, self.on_apply)

        n_col, n_span = 2, 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(widgets_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.widgets_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_add_widgets, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_check_all_widgets, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(general_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_general_zoom_1d, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_general_hover_mode, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_general_figure_width, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_general_figure_height, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(color_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_color_colorblind, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_color_colormap, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotations_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_annotations_all, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_annotations_show, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_annotations_font_size, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_annotations_rotate, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_annotations_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_annotations_offset_y, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_legend_all, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_legend_show, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_legend_transparency, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_legend_orientation, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_legend_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_scatter_all, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_scatter_size, (n, 0), flag=wx.EXPAND)
        grid.Add(self.widgets_scatter_transparency, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_add_custom_widgets(self, _evt):
        """Enable custom widgets"""

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
                self.scrolledPanel = PanelWidgetsSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
