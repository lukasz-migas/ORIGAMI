"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1

# from origami.config.config import CONFIG
from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelGeneralSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_frame_height, bokeh_frame_width, bokeh_frame_title_font_size = None, None, None
    bokeh_frame_label_font_size, bokeh_frame_label_font_weight, bokeh_frame_tick_font_size = None, None, None
    bokeh_frame_label_y_axis, bokeh_frame_tick_labels_x_axis, bokeh_frame_border_min_top = None, None, None
    bokeh_frame_tick_labels_y_axis, bokeh_frame_tick_x_axis, bokeh_frame_border_min_bottom = None, None, None
    bokeh_frame_tick_y_axis, bokeh_frame_border_min_left, bokeh_frame_border_min_right = None, None, None
    bokeh_frame_outline_width, bokeh_frame_outline_alpha, bokeh_frame_background_color = None, None, None
    bokeh_frame_grid_line, bokeh_frame_grid_line_color, bokeh_frame_title_font_weight = None, None, None
    bokeh_frame_label_x_axis = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        figure_height_label = make_static_text(self, "Height (px):")
        self.bokeh_frame_height = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=2000, inc=100, size=(70, -1))
        self.bokeh_frame_height.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        figure_width_label = make_static_text(self, "Width (px):")
        self.bokeh_frame_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=2000, inc=100, size=(70, -1))
        self.bokeh_frame_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        title_fontsize_label = make_static_text(self, "Title font size")
        self.bokeh_frame_title_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.bokeh_frame_title_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bokeh_frame_title_font_size.SetToolTip(wx.ToolTip("Title font size. Value in points."))

        self.bokeh_frame_title_font_weight = make_checkbox(self, "bold", name="frame")
        self.bokeh_frame_title_font_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.bokeh_frame_title_font_weight, "Font weight of the title element")

        label_fontsize_label = make_static_text(self, "Label font size")
        self.bokeh_frame_label_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.bokeh_frame_label_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        set_tooltip(self.bokeh_frame_label_font_size, "Font size of the labels - value in points")

        self.bokeh_frame_label_font_weight = make_checkbox(self, "bold", name="frame")
        self.bokeh_frame_label_font_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.bokeh_frame_label_font_weight, "Font weight of the labels")

        ticks_fontsize_label = make_static_text(self, "Tick font size")
        self.bokeh_frame_tick_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.bokeh_frame_tick_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bokeh_frame_tick_font_size.SetToolTip(wx.ToolTip("Tick font size. Value in points."))

        label_label = wx.StaticText(self, -1, "Label:")
        self.bokeh_frame_label_x_axis = make_checkbox(self, "x-axis", name="frame")
        self.bokeh_frame_label_x_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_label_x_axis.SetToolTip(wx.ToolTip("Show labels on the x-axis."))

        self.bokeh_frame_label_y_axis = make_checkbox(self, "y-axis", name="frame")
        self.bokeh_frame_label_y_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_label_y_axis.SetToolTip(wx.ToolTip("Show labels on the y-axis."))

        tick_labels_label = wx.StaticText(self, -1, "Tick labels:")
        self.bokeh_frame_tick_labels_x_axis = make_checkbox(self, "x-axis", name="frame")
        self.bokeh_frame_tick_labels_x_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_tick_labels_x_axis.SetToolTip(wx.ToolTip("Show tick labels on the x-axis"))

        self.bokeh_frame_tick_labels_y_axis = make_checkbox(self, "y-axis", name="frame")
        self.bokeh_frame_tick_labels_y_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_tick_labels_y_axis.SetToolTip(wx.ToolTip("Show tick labels on the y-axis"))

        ticks_label = wx.StaticText(self, -1, "Ticks:")
        self.bokeh_frame_tick_x_axis = make_checkbox(self, "x-axis", name="frame")
        self.bokeh_frame_tick_x_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_tick_x_axis.SetToolTip(wx.ToolTip("Show ticks on the x-axis"))

        self.bokeh_frame_tick_y_axis = make_checkbox(self, "y-axis", name="frame")
        self.bokeh_frame_tick_y_axis.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_tick_y_axis.SetToolTip(wx.ToolTip("Show ticks on the y-axis"))

        border_left_label = make_static_text(self, "Border left")
        self.bokeh_frame_border_min_left = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.bokeh_frame_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.bokeh_frame_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_right_label = make_static_text(self, "Border right")
        self.bokeh_frame_border_min_right = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.bokeh_frame_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.bokeh_frame_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_top_label = make_static_text(self, "Border top")
        self.bokeh_frame_border_min_top = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.bokeh_frame_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.bokeh_frame_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_bottom_label = make_static_text(self, "Border bottom")
        self.bokeh_frame_border_min_bottom = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.bokeh_frame_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.bokeh_frame_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        outline_width_label = make_static_text(self, "Outline width")
        self.bokeh_frame_outline_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50, -1))
        self.bokeh_frame_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
        self.bokeh_frame_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        outline_transparency_label = make_static_text(self, "Outline alpha")
        self.bokeh_frame_outline_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.05, size=(50, -1))
        self.bokeh_frame_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
        self.bokeh_frame_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        frame_background_color = make_static_text(self, "Background color")
        self.bokeh_frame_background_color = wx.Button(self, wx.ID_ANY, size=wx.Size(26, 26), name="background_color")
        self.bokeh_frame_background_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        frame_gridline_label = make_static_text(self, "Grid lines:")
        self.bokeh_frame_grid_line = make_checkbox(self, "show")
        self.bokeh_frame_grid_line.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bokeh_frame_grid_line.SetToolTip(wx.ToolTip("Show gridlines in the plot area."))

        frame_gridline_color = make_static_text(self, "Grid color")
        self.bokeh_frame_grid_line_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="gridline_color")
        self.bokeh_frame_grid_line_color.Bind(wx.EVT_BUTTON, self.on_assign_color)
        self.bokeh_frame_grid_line_color.SetToolTip(
            wx.ToolTip("Gridlines color. Only takes effect if gridlines are shown.")
        )

        figure_parameters_label = wx.StaticText(self, -1, "Figure parameters")
        set_item_font(figure_parameters_label)

        frame_parameters_label = wx.StaticText(self, -1, "Frame parameters")
        set_item_font(frame_parameters_label)

        n_col, n_span = 3, 2
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(figure_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(figure_height_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_height, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(figure_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(title_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_title_font_size, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_frame_title_font_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(label_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_label_font_size, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_frame_label_font_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(ticks_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_tick_font_size, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_label_x_axis, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_frame_label_y_axis, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tick_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_tick_labels_x_axis, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.bokeh_frame_tick_labels_y_axis, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(ticks_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_tick_x_axis, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_frame_tick_y_axis, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(border_left_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_border_min_left, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_right_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_border_min_right, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_top_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_border_min_top, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_bottom_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_border_min_bottom, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(outline_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_outline_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(outline_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_outline_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_background_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_background_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_gridline_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_grid_line, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_gridline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_frame_grid_line_color, (n, 1), flag=wx.EXPAND)

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

        # update configuration and button color
        if source == "background_color":
            self.bokeh_frame_background_color.SetBackgroundColour(color_255)
        elif source == "gridline_color":
            self.bokeh_frame_grid_line_color.SetBackgroundColour(color_255)

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {
            "bokeh_frame_width": int(self.bokeh_frame_width.GetValue()),
            "bokeh_frame_height": int(self.bokeh_frame_height.GetValue()),
            "bokeh_frame_outline_width": self.bokeh_frame_outline_width.GetValue(),
            "bokeh_frame_outline_alpha": self.bokeh_frame_outline_alpha.GetValue(),
            "bokeh_frame_border_min_left": int(self.bokeh_frame_border_min_left.GetValue()),
            "bokeh_frame_border_min_right": int(self.bokeh_frame_border_min_right.GetValue()),
            "bokeh_frame_border_min_top": int(self.bokeh_frame_border_min_top.GetValue()),
            "bokeh_frame_border_min_bottom": int(self.bokeh_frame_border_min_bottom.GetValue()),
            "bokeh_frame_background_color": convert_rgb_255_to_1(
                self.bokeh_frame_background_color.GetBackgroundColour()
            ),
            "bokeh_frame_grid_line": self.bokeh_frame_grid_line.GetValue(),
            "bokeh_frame_grid_line_color": convert_rgb_255_to_1(self.bokeh_frame_grid_line_color.GetBackgroundColour()),
            "bokeh_frame_title_font_size": self.bokeh_frame_title_font_size.GetValue(),
            "bokeh_frame_title_font_weight": self.bokeh_frame_title_font_weight.GetValue(),
            "bokeh_frame_label_font_size": self.bokeh_frame_label_font_size.GetValue(),
            "bokeh_frame_label_font_weight": self.bokeh_frame_label_font_weight.GetValue(),
            "bokeh_frame_label_x_axis": self.bokeh_frame_label_x_axis.GetValue(),
            "bokeh_frame_label_y_axis": self.bokeh_frame_label_y_axis.GetValue(),
            "bokeh_frame_tick_font_size": self.bokeh_frame_tick_font_size.GetValue(),
            "bokeh_frame_tick_x_axis": self.bokeh_frame_tick_x_axis.GetValue(),
            "bokeh_frame_tick_y_axis": self.bokeh_frame_tick_y_axis.GetValue(),
            "bokeh_frame_tick_labels_x_axis": self.bokeh_frame_tick_labels_x_axis.GetValue(),
            "bokeh_frame_tick_labels_y_axis": self.bokeh_frame_tick_labels_y_axis.GetValue(),
            # "bokeh_frame_tick_use_scientific": self.bokeh_frame_tick_use_scientific.GetValue(),
            # "bokeh_frame_tick_precision": self.bokeh_frame_tick_precision.GetValue(),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_frame_width.SetValue(config.get("bokeh_frame_width", CONFIG.bokeh_frame_width))
        self.bokeh_frame_height.SetValue(config.get("bokeh_frame_height", CONFIG.bokeh_frame_height))
        self.bokeh_frame_outline_width.SetValue(
            config.get("bokeh_frame_outline_width", CONFIG.bokeh_frame_outline_width)
        )
        self.bokeh_frame_outline_alpha.SetValue(
            config.get("bokeh_frame_outline_alpha", CONFIG.bokeh_frame_outline_alpha)
        )
        self.bokeh_frame_border_min_left.SetValue(
            config.get("bokeh_frame_border_min_left", CONFIG.bokeh_frame_border_min_left)
        )
        self.bokeh_frame_border_min_right.SetValue(
            config.get("bokeh_frame_border_min_right", CONFIG.bokeh_frame_border_min_right)
        )
        self.bokeh_frame_border_min_top.SetValue(
            config.get("bokeh_frame_border_min_top", CONFIG.bokeh_frame_border_min_top)
        )
        self.bokeh_frame_border_min_bottom.SetValue(
            config.get("bokeh_frame_border_min_bottom", CONFIG.bokeh_frame_border_min_bottom)
        )
        self.bokeh_frame_background_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_frame_background_color", CONFIG.bokeh_frame_background_color))
        )
        self.bokeh_frame_grid_line.SetValue(config.get("bokeh_frame_grid_line", CONFIG.bokeh_frame_grid_line))
        self.bokeh_frame_grid_line_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_frame_grid_line_color", CONFIG.bokeh_frame_grid_line_color))
        )
        self.bokeh_frame_title_font_size.SetValue(
            config.get("bokeh_frame_title_font_size", CONFIG.bokeh_frame_title_font_size)
        )
        self.bokeh_frame_title_font_weight.SetValue(
            config.get("bokeh_frame_title_font_weight", CONFIG.bokeh_frame_title_font_weight)
        )
        self.bokeh_frame_label_font_size.SetValue(
            config.get("bokeh_frame_label_font_size", CONFIG.bokeh_frame_label_font_size)
        )
        self.bokeh_frame_label_font_weight.SetValue(
            config.get("bokeh_frame_label_font_weight", CONFIG.bokeh_frame_label_font_weight)
        )
        self.bokeh_frame_label_x_axis.SetValue(config.get("bokeh_frame_label_x_axis", CONFIG.bokeh_frame_label_x_axis))
        self.bokeh_frame_label_y_axis.SetValue(config.get("bokeh_frame_label_y_axis", CONFIG.bokeh_frame_label_y_axis))
        self.bokeh_frame_tick_font_size.SetValue(
            config.get("bokeh_frame_tick_font_size", CONFIG.bokeh_frame_tick_font_size)
        )
        self.bokeh_frame_tick_x_axis.SetValue(config.get("bokeh_frame_tick_x_axis", CONFIG.bokeh_frame_tick_x_axis))
        self.bokeh_frame_tick_y_axis.SetValue(config.get("bokeh_frame_tick_y_axis", CONFIG.bokeh_frame_tick_y_axis))
        self.bokeh_frame_tick_labels_x_axis.SetValue(
            config.get("bokeh_frame_tick_labels_x_axis", CONFIG.bokeh_frame_tick_labels_x_axis)
        )
        self.bokeh_frame_tick_labels_y_axis.SetValue(
            config.get("bokeh_frame_tick_labels_y_axis", CONFIG.bokeh_frame_tick_labels_y_axis)
        )
        # self.bokeh_frame_tick_use_scientific.SetValue(
        #     config.get("bokeh_frame_tick_use_scientific", CONFIG.bokeh_frame_tick_use_scientific)
        # )
        # self.bokeh_frame_tick_precision.SetValue(
        #     config.get("bokeh_frame_tick_precision", CONFIG.bokeh_frame_tick_precision)
        # )
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelGeneralSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
