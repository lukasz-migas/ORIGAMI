"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelWidgetsSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_widgets_position, bokeh_widgets_add_js, widgets_check_all_widgets = None, None, None
    bokeh_widgets_general_hover, bokeh_widgets_general_width, widgets_legend_all = None, None, None
    bokeh_widgets_general_height, bokeh_widgets_color_colorblind, widgets_annotations_all = None, None, None
    bokeh_widgets_color_colormap, bokeh_widgets_annotation_font_offset_y, bokeh_widgets_legend_show = None, None, None
    bokeh_widgets_annotation_show, bokeh_widgets_annotation_font_size, bokeh_widgets_legend_alpha = None, None, None
    bokeh_widgets_annotation_font_rotation, bokeh_widgets_annotation_font_offset_x = None, None
    bokeh_widgets_legend_position, widgets_scatter_all, bokeh_widgets_scatter_size = None, None, None
    bokeh_widgets_scatter_alpha, bokeh_widgets_legend_orientation, widgets_general_all = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        widgets_position = make_static_text(self, "Widget position:")
        self.bokeh_widgets_position = wx.ComboBox(
            self, -1, style=wx.CB_READONLY, choices=CONFIG.bokeh_widgets_position_choices
        )
        self.bokeh_widgets_position.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.bokeh_widgets_add_js = make_checkbox(self, "Add custom JS widgets")
        self.bokeh_widgets_add_js.Bind(wx.EVT_CHECKBOX, self.on_add_custom_widgets)

        self.widgets_check_all_widgets = make_checkbox(self, "Check/uncheck all")
        self.widgets_check_all_widgets.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        # general
        general_label = wx.StaticText(self, -1, "General widgets")
        set_item_font(general_label)

        self.widgets_general_all = make_checkbox(self, "All/None general widgets")
        self.widgets_general_all.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.bokeh_widgets_general_hover = make_checkbox(self, "Hover mode toggle", name="hover_mode")
        self.bokeh_widgets_general_hover.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_general_width = make_checkbox(self, "Figure width", name="figure_width")
        self.bokeh_widgets_general_width.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_general_height = make_checkbox(self, "Figure height", name="figure_height")
        self.bokeh_widgets_general_height.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # color
        color_label = wx.StaticText(self, -1, "Color widgets")
        set_item_font(color_label)

        self.bokeh_widgets_color_colorblind = make_checkbox(self, "Colorblind toggle")
        self.bokeh_widgets_color_colorblind.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_color_colormap = make_checkbox(self, "Colormap dropdown")
        self.bokeh_widgets_color_colormap.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # labels
        annotations_label = wx.StaticText(self, -1, "Label and annotation widgets")
        set_item_font(annotations_label)

        self.widgets_annotations_all = make_checkbox(self, "All/None annotation widgets")
        self.widgets_annotations_all.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.bokeh_widgets_annotation_show = make_checkbox(self, "Show/hide toggle", name="annotations_toggle")
        self.bokeh_widgets_annotation_show.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_annotation_font_size = make_checkbox(self, "Font size slider", name="annotations_font_size")
        self.bokeh_widgets_annotation_font_size.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_annotation_font_rotation = make_checkbox(
            self, "Rotation slider", name="annotations_rotation"
        )
        self.bokeh_widgets_annotation_font_rotation.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_annotation_font_offset_x = make_checkbox(
            self, "Horizontal offset slider", name="annotations_offset_x"
        )
        self.bokeh_widgets_annotation_font_offset_x.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_annotation_font_offset_y = make_checkbox(
            self, "Vertical offset slider", name="annotations_offset_y"
        )
        self.bokeh_widgets_annotation_font_offset_y.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # labels
        legend_label = wx.StaticText(self, -1, "Legend widgets")
        set_item_font(legend_label)

        self.widgets_legend_all = make_checkbox(self, "All/None legend widgets")
        self.widgets_legend_all.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.bokeh_widgets_legend_show = make_checkbox(self, "Show/hide toggle", name="legend_name")
        self.bokeh_widgets_legend_show.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_legend_alpha = make_checkbox(self, "Legend transparency", name="legend_transparency")
        self.bokeh_widgets_legend_alpha.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_legend_orientation = make_checkbox(self, "Legend rotation", name="legend_orientation")
        self.bokeh_widgets_legend_orientation.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_legend_position = make_checkbox(self, "Legend position", name="legend_position")
        self.bokeh_widgets_legend_position.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # scatter
        scatter_label = wx.StaticText(self, -1, "Scatter widgets")
        set_item_font(scatter_label)

        self.widgets_scatter_all = make_checkbox(self, "All/None scatter widgets")
        self.widgets_scatter_all.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.bokeh_widgets_scatter_size = make_checkbox(self, "Size slider", name="scatter_size")
        self.bokeh_widgets_scatter_size.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_widgets_scatter_alpha = make_checkbox(self, "Transparency slider", name="scatter_transparency")
        self.bokeh_widgets_scatter_alpha.Bind(wx.EVT_CHECKBOX, self.on_apply)

        n_col, n_span = 2, 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(widgets_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.bokeh_widgets_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_add_js, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_check_all_widgets, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(general_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_general_all, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_general_hover, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_general_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_general_height, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(color_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_color_colorblind, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_color_colormap, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotations_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_annotations_all, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_annotation_show, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_annotation_font_size, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_annotation_font_rotation, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_annotation_font_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_annotation_font_offset_y, (n, 0), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_legend_all, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_legend_show, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_legend_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_legend_orientation, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_legend_position, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scatter_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(self.widgets_scatter_all, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_widgets_scatter_size, (n, 0), flag=wx.EXPAND)
        grid.Add(self.bokeh_widgets_scatter_alpha, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_add_custom_widgets(self, _evt):
        """Enable custom widgets"""

    def on_toggle_controls(self, evt):
        """Toggle controls"""
        check_all = self.widgets_check_all_widgets.GetValue()
        check_general = self.widgets_general_all.GetValue()
        check_annotations = self.widgets_annotations_all.GetValue()
        check_legend = self.widgets_legend_all.GetValue()
        check_scatter = self.widgets_scatter_all.GetValue()
        if check_all:
            check_general, check_annotations, check_legend, check_scatter = True, True, True, True

        # check general
        self.bokeh_widgets_general_hover.SetValue(check_general)
        self.bokeh_widgets_general_height.SetValue(check_general)
        self.bokeh_widgets_general_width.SetValue(check_general)

        # check annotations
        self.bokeh_widgets_annotation_show.SetValue(check_annotations)
        self.bokeh_widgets_annotation_font_size.SetValue(check_annotations)
        self.bokeh_widgets_annotation_font_rotation.SetValue(check_annotations)
        self.bokeh_widgets_annotation_font_offset_x.SetValue(check_annotations)
        self.bokeh_widgets_annotation_font_offset_y.SetValue(check_annotations)

        # check legend
        self.bokeh_widgets_legend_show.SetValue(check_legend)
        self.bokeh_widgets_legend_alpha.SetValue(check_legend)
        self.bokeh_widgets_legend_orientation.SetValue(check_legend)
        self.bokeh_widgets_legend_position.SetValue(check_legend)

        # check scatter
        self.bokeh_widgets_scatter_size.SetValue(check_scatter)
        self.bokeh_widgets_scatter_alpha.SetValue(check_scatter)

        self._parse_evt(evt)

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {
            "bokeh_widgets_position": self.bokeh_widgets_position.GetStringSelection(),
            "bokeh_widgets_add_js": self.bokeh_widgets_add_js.GetValue(),
            "bokeh_widgets_general_hover": self.bokeh_widgets_general_hover.GetValue(),
            "bokeh_widgets_general_width": self.bokeh_widgets_general_width.GetValue(),
            "bokeh_widgets_general_height": self.bokeh_widgets_general_height.GetValue(),
            "bokeh_widgets_color_colorblind": self.bokeh_widgets_color_colorblind.GetValue(),
            "bokeh_widgets_color_colormap": self.bokeh_widgets_color_colormap.GetValue(),
            "bokeh_widgets_annotation_show": self.bokeh_widgets_annotation_show.GetValue(),
            "bokeh_widgets_annotation_font_size": self.bokeh_widgets_annotation_font_size.GetValue(),
            "bokeh_widgets_annotation_font_rotation": self.bokeh_widgets_annotation_font_rotation.GetValue(),
            "bokeh_widgets_annotation_font_offset_x": self.bokeh_widgets_annotation_font_offset_x.GetValue(),
            "bokeh_widgets_annotation_font_offset_y": self.bokeh_widgets_annotation_font_offset_y.GetValue(),
            "bokeh_widgets_legend_show": self.bokeh_widgets_legend_show.GetValue(),
            "bokeh_widgets_legend_alpha": self.bokeh_widgets_legend_alpha.GetValue(),
            "bokeh_widgets_legend_orientation": self.bokeh_widgets_legend_orientation.GetValue(),
            "bokeh_widgets_legend_position": self.bokeh_widgets_legend_position.GetValue(),
            "bokeh_widgets_scatter_size": self.bokeh_widgets_scatter_size.GetValue(),
            "bokeh_widgets_scatter_alpha": self.bokeh_widgets_scatter_alpha.GetValue(),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_widgets_position.SetStringSelection(
            config.get("bokeh_widgets_position", CONFIG.bokeh_widgets_position)
        )
        self.bokeh_widgets_add_js.SetValue(config.get("bokeh_widgets_add_js", CONFIG.bokeh_widgets_add_js))
        self.bokeh_widgets_general_hover.SetValue(
            config.get("bokeh_widgets_general_hover", CONFIG.bokeh_widgets_general_hover)
        )
        self.bokeh_widgets_general_width.SetValue(
            config.get("bokeh_widgets_general_width", CONFIG.bokeh_widgets_general_width)
        )
        self.bokeh_widgets_general_height.SetValue(
            config.get("bokeh_widgets_general_height", CONFIG.bokeh_widgets_general_height)
        )
        self.bokeh_widgets_color_colorblind.SetValue(
            config.get("bokeh_widgets_color_colorblind", CONFIG.bokeh_widgets_color_colorblind)
        )
        self.bokeh_widgets_color_colormap.SetValue(
            config.get("bokeh_widgets_color_colormap", CONFIG.bokeh_widgets_color_colormap)
        )
        self.bokeh_widgets_annotation_show.SetValue(
            config.get("bokeh_widgets_annotation_show", CONFIG.bokeh_widgets_annotation_show)
        )
        self.bokeh_widgets_annotation_font_size.SetValue(
            config.get("bokeh_widgets_annotation_font_size", CONFIG.bokeh_widgets_annotation_font_size)
        )
        self.bokeh_widgets_annotation_font_rotation.SetValue(
            config.get("bokeh_widgets_annotation_font_rotation", CONFIG.bokeh_widgets_annotation_font_rotation)
        )
        self.bokeh_widgets_annotation_font_offset_x.SetValue(
            config.get("bokeh_widgets_annotation_font_offset_x", CONFIG.bokeh_widgets_annotation_font_offset_x)
        )
        self.bokeh_widgets_annotation_font_offset_y.SetValue(
            config.get("bokeh_widgets_annotation_font_offset_y", CONFIG.bokeh_widgets_annotation_font_offset_y)
        )
        self.bokeh_widgets_legend_show.SetValue(
            config.get("bokeh_widgets_legend_show", CONFIG.bokeh_widgets_legend_show)
        )
        self.bokeh_widgets_legend_alpha.SetValue(
            config.get("bokeh_widgets_legend_alpha", CONFIG.bokeh_widgets_legend_alpha)
        )
        self.bokeh_widgets_legend_orientation.SetValue(
            config.get("bokeh_widgets_legend_orientation", CONFIG.bokeh_widgets_legend_orientation)
        )
        self.bokeh_widgets_legend_position.SetValue(
            config.get("bokeh_widgets_legend_position", CONFIG.bokeh_widgets_legend_position)
        )
        self.bokeh_widgets_scatter_size.SetValue(
            config.get("bokeh_widgets_scatter_size", CONFIG.bokeh_widgets_scatter_size)
        )
        self.bokeh_widgets_scatter_alpha.SetValue(
            config.get("bokeh_widgets_scatter_alpha", CONFIG.bokeh_widgets_scatter_alpha)
        )
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelWidgetsSettings(self, None)

        app = App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
