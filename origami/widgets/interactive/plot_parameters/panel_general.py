"""Legend panel"""
# Third-party imports
import wx

# Local imports
# from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGeneralSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    figure_height_label, figure_width_label, title_fontsize_label, frame_title_weight = None, None, None, None
    label_fontsize_label, frame_label_weight, ticks_fontsize_label, frame_label_xaxis_check = None, None, None, None
    frame_label_yaxis_check, frame_tick_labels_xaxis_check, frame_border_min_top = None, None, None
    frame_tick_labels_yaxis_check, frame_ticks_xaxis_check, frame_border_min_bottom = None, None, None
    frame_ticks_yaxis_check, frame_border_min_left, frame_border_min_right = None, None, None
    frame_outline_width, frame_outline_alpha, frame_background_color_btn = None, None, None
    frame_gridline_check, frame_gridline_color_btn = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        figure_height_label = make_static_text(self, "Height (px):")
        self.figure_height_label = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=2000, inc=100, size=(70, -1))
        self.figure_height_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        figure_width_label = make_static_text(self, "Width (px):")
        self.figure_width_label = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=2000, inc=100, size=(70, -1))
        self.figure_width_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        title_fontsize_label = make_static_text(self, "Title font size")
        self.title_fontsize_label = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.title_fontsize_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.title_fontsize_label.SetToolTip(wx.ToolTip("Title font size. Value in points."))

        self.frame_title_weight = make_checkbox(self, "bold", name="frame")
        self.frame_title_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.frame_title_weight, "Font weight of the title element")

        label_fontsize_label = make_static_text(self, "Label font size")
        self.label_fontsize_label = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.label_fontsize_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        set_tooltip(self.label_fontsize_label, "Font size of the labels - value in points")

        self.frame_label_weight = make_checkbox(self, "bold", name="frame")
        self.frame_label_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.frame_label_weight, "Font weight of the labels")

        ticks_fontsize_label = make_static_text(self, "Tick font size")
        self.ticks_fontsize_label = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.ticks_fontsize_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.ticks_fontsize_label.SetToolTip(wx.ToolTip("Tick font size. Value in points."))

        label_label = wx.StaticText(self, -1, "Label:")
        self.frame_label_xaxis_check = make_checkbox(self, "x-axis", name="frame")
        self.frame_label_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_label_xaxis_check.SetToolTip(wx.ToolTip("Show labels on the x-axis."))

        self.frame_label_yaxis_check = make_checkbox(self, "y-axis", name="frame")
        self.frame_label_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_label_yaxis_check.SetToolTip(wx.ToolTip("Show labels on the y-axis."))

        tick_labels_label = wx.StaticText(self, -1, "Tick labels:")
        self.frame_tick_labels_xaxis_check = make_checkbox(self, "x-axis", name="frame")
        self.frame_tick_labels_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_tick_labels_xaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the x-axis"))

        self.frame_tick_labels_yaxis_check = make_checkbox(self, "y-axis", name="frame")
        self.frame_tick_labels_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_tick_labels_yaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the y-axis"))

        ticks_label = wx.StaticText(self, -1, "Ticks:")
        self.frame_ticks_xaxis_check = make_checkbox(self, "x-axis", name="frame")
        self.frame_ticks_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_ticks_xaxis_check.SetToolTip(wx.ToolTip("Show ticks on the x-axis"))

        self.frame_ticks_yaxis_check = make_checkbox(self, "y-axis", name="frame")
        self.frame_ticks_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_ticks_yaxis_check.SetToolTip(wx.ToolTip("Show ticks on the y-axis"))

        border_left_label = make_static_text(self, "Border left")
        self.frame_border_min_left = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.frame_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_right_label = make_static_text(self, "Border right")
        self.frame_border_min_right = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.frame_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_top_label = make_static_text(self, "Border top")
        self.frame_border_min_top = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.frame_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        border_bottom_label = make_static_text(self, "Border bottom")
        self.frame_border_min_bottom = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, inc=5, size=(50, -1))
        self.frame_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        outline_width_label = make_static_text(self, "Outline width")
        self.frame_outline_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50, -1))
        self.frame_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
        self.frame_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        outline_transparency_label = make_static_text(self, "Outline alpha")
        self.frame_outline_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.05, size=(50, -1))
        self.frame_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
        self.frame_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        frame_background_color = make_static_text(self, "Background color")
        self.frame_background_color_btn = wx.Button(self, wx.ID_ANY, size=wx.Size(26, 26), name="background_color")
        self.frame_background_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        frame_gridline_label = make_static_text(self, "Grid lines:")
        self.frame_gridline_check = make_checkbox(self, "show")
        self.frame_gridline_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.frame_gridline_check.SetToolTip(wx.ToolTip("Show gridlines in the plot area."))

        frame_gridline_color = make_static_text(self, "Grid color")
        self.frame_gridline_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="gridline_color")
        self.frame_gridline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)
        self.frame_gridline_color_btn.SetToolTip(
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
        grid.Add(self.figure_height_label, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(figure_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.figure_width_label, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(title_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.title_fontsize_label, (n, 1), flag=wx.EXPAND)
        grid.Add(self.frame_title_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(label_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_fontsize_label, (n, 1), flag=wx.EXPAND)
        grid.Add(self.frame_label_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(ticks_fontsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ticks_fontsize_label, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_label_xaxis_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.frame_label_yaxis_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tick_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_tick_labels_xaxis_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.frame_tick_labels_yaxis_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(ticks_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_ticks_xaxis_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.frame_ticks_yaxis_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(border_left_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_border_min_left, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_right_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_border_min_right, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_top_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_border_min_top, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(border_bottom_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_border_min_bottom, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(outline_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_outline_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(outline_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_outline_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_background_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_background_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_gridline_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_gridline_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(frame_gridline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_gridline_color_btn, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color

        # source, color_255, color_1 = self._on_assign_color(evt)

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
                self.scrolledPanel = PanelGeneralSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
