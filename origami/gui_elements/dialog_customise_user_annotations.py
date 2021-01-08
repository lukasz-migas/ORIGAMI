"""Control dialog for extra annotation parameters"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox


class DialogCustomiseUserAnnotations(Dialog):
    """Customise extra annotation parameters"""

    # ui elements
    arrow_line_width_value = None
    arrow_line_style_value = None
    arrow_cap_length_value = None
    arrow_cap_width_value = None
    label_y_axis_offset_value = None
    label_font_size_value = None
    label_font_weight_value = None
    label_vert_alignment_value = None
    label_horz_alignment_value = None
    label_fontOrientation_value = None
    zoom_y_buffer_check = None
    zoom_y_buffer_value = None
    highlight_alpha_value = None
    highlight_width_value = None

    def __init__(self, parent):
        Dialog.__init__(self, parent, title="Annotation...")

        self.make_gui()
        self.CentreOnParent()

    def on_ok(self, _evt):
        """Close window with OK exit"""
        self.EndModal(wx.OK)

    def make_gui(self):
        """Make gui panel"""
        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    # noinspection DuplicatedCode
    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        self.arrow_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_arrow_line_width),
            min=0.005,
            max=2,
            initial=CONFIG.annotation_arrow_line_width,
            inc=0.25,
            size=(-1, -1),
        )
        self.arrow_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.arrow_line_style_value = wx.Choice(panel, -1, choices=CONFIG.lineStylesList, size=(-1, -1))
        self.arrow_line_style_value.SetStringSelection(CONFIG.annotation_arrow_line_style)
        self.arrow_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.arrow_cap_length_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_arrow_cap_length),
            min=0.0,
            max=1000,
            initial=CONFIG.annotation_arrow_cap_length,
            inc=0.1,
            size=(-1, -1),
        )
        self.arrow_cap_length_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.arrow_cap_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_arrow_cap_width),
            min=0.0,
            max=1000,
            initial=CONFIG.annotation_arrow_cap_width,
            inc=0.1,
            size=(-1, -1),
        )
        self.arrow_cap_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.label_y_axis_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_label_y_offset),
            min=0.0,
            max=1000,
            initial=CONFIG.annotation_label_y_offset,
            inc=0.05,
            size=(-1, -1),
        )
        self.label_y_axis_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.label_fontOrientation_value = wx.Choice(
            panel, -1, choices=CONFIG.label_font_orientation_list, size=(-1, -1)
        )
        self.label_fontOrientation_value.SetStringSelection(CONFIG.annotation_label_font_orientation)
        self.label_fontOrientation_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.label_font_size_value = wx.Choice(panel, -1, choices=CONFIG.label_fontsize_list, size=(-1, -1))
        self.label_font_size_value.SetStringSelection(CONFIG.annotation_label_font_size)
        self.label_font_size_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.label_font_weight_value = wx.Choice(panel, -1, choices=CONFIG.label_fontweight_list, size=(-1, -1))
        self.label_font_weight_value.SetStringSelection(CONFIG.annotation_label_font_weight)
        self.label_font_weight_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.label_horz_alignment_value = wx.Choice(panel, -1, choices=CONFIG.horizontal_alignment_list, size=(-1, -1))
        self.label_horz_alignment_value.SetStringSelection(CONFIG.annotation_label_horz)
        self.label_horz_alignment_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.label_vert_alignment_value = wx.Choice(panel, -1, choices=CONFIG.vertical_alignment_list, size=(-1, -1))
        self.label_vert_alignment_value.SetStringSelection(CONFIG.annotation_label_vert)
        self.label_vert_alignment_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.zoom_y_buffer_check = make_checkbox(panel, "")
        self.zoom_y_buffer_check.SetValue(CONFIG.annotation_zoom_y)

        self.zoom_y_buffer_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_zoom_y_multiplier),
            min=1,
            max=3,
            initial=CONFIG.annotation_zoom_y_multiplier,
            inc=0.1,
            size=(-1, -1),
        )
        self.zoom_y_buffer_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.highlight_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_patch_transparency),
            min=0.0,
            max=1.0,
            initial=CONFIG.annotation_patch_transparency,
            inc=0.2,
            size=(-1, -1),
        )
        self.highlight_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.highlight_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotation_patch_width),
            min=1.0,
            max=10.0,
            initial=CONFIG.annotation_patch_width,
            inc=1,
            size=(-1, -1),
        )
        self.highlight_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(wx.StaticText(panel, -1, "Arrow line width:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_width_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Arrow line style:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_style_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Arrow cap length:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_cap_length_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Arrow cap width:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_cap_width_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Y-axis label offset:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.label_y_axis_offset_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Font orientation:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_fontOrientation_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Font size:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_font_size_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Font weight:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_font_weight_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Label horizontal alignment:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.label_horz_alignment_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Label vertical alignment:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.label_vert_alignment_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Adjust y-axis zoom:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.zoom_y_buffer_check, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Zoom y-axis multiplier:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.zoom_y_buffer_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(panel, -1, "Highlight transparency:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.highlight_alpha_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Highlight width:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.highlight_width_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_apply(self, _evt):
        """Update configuration with new values"""
        CONFIG.annotation_arrow_line_width = self.arrow_line_width_value.GetValue()
        CONFIG.annotation_arrow_line_style = self.arrow_line_style_value.GetStringSelection()
        CONFIG.annotation_arrow_cap_length = self.arrow_cap_length_value.GetValue()
        CONFIG.annotation_arrow_cap_width = self.arrow_cap_width_value.GetValue()

        CONFIG.annotation_label_y_offset = self.label_y_axis_offset_value.GetValue()
        CONFIG.annotation_label_font_size = self.label_font_size_value.GetStringSelection()
        CONFIG.annotation_label_font_weight = self.label_font_weight_value.GetStringSelection()
        CONFIG.annotation_label_vert = self.label_vert_alignment_value.GetStringSelection()
        CONFIG.annotation_label_horz = self.label_horz_alignment_value.GetStringSelection()
        CONFIG.annotation_label_font_orientation = self.label_fontOrientation_value.GetStringSelection()

        CONFIG.annotation_zoom_y = self.zoom_y_buffer_check.GetValue()
        CONFIG.annotation_zoom_y_multiplier = self.zoom_y_buffer_value.GetValue()

        CONFIG.annotation_patch_transparency = self.highlight_alpha_value.GetValue()
        CONFIG.annotation_patch_width = self.highlight_width_value.GetValue()


def _main():

    from origami.app import App

    app = App()
    ex = DialogCustomiseUserAnnotations(None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
