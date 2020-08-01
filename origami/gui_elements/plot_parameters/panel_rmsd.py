"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.styles import set_tooltip
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelRMSDSettings(PanelSettingsBase):
    """Violin settings"""

    rmsd_position_value, rmsd_fontsize_value, rmsd_font_weight_check = None, None, None
    rmsd_x_rotation_value, rmsd_y_rotation_value, rmsd_line_style_value = None, None, None
    rmsd_line_hatch_value, rmsd_alpha_value, rmsd_vspace_value = None, None, None
    rmsd_add_labels_check, rmsd_matrix_color_fmt, rmsd_matrix_font_weight_check = None, None, None
    rmsd_matrix_fontsize, rmsd_matrix_font_color_btn, rmsd_x_position_value = None, None, None
    rmsd_y_position_value, rmsd_color_btn, rmsd_line_width_value = None, None, None
    rmsd_color_line_btn, rmsd_underline_color_btn = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        rmsd_position_label = wx.StaticText(self, -1, "Position:")
        self.rmsd_position_value = wx.Choice(self, -1, choices=CONFIG.rmsd_position_choices, size=(-1, -1))
        self.rmsd_position_value.SetStringSelection(CONFIG.rmsd_position)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self._recalculate_rmsd_position)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_update_rmsd_label)

        rmsd_x_position = wx.StaticText(self, -1, "Position X:")
        self.rmsd_x_position_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1)
        )
        self.rmsd_x_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._recalculate_rmsd_position)
        self.rmsd_x_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        rmsd_y_position = wx.StaticText(self, -1, "Position Y:")
        self.rmsd_y_position_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1)
        )
        self.rmsd_y_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._recalculate_rmsd_position)
        self.rmsd_y_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        rmsd_fontsize = wx.StaticText(self, -1, "Label size:")
        self.rmsd_fontsize_value = wx.SpinCtrlDouble(
            self, -1, value=str(CONFIG.rmsd_fontSize), min=1, max=50, initial=0, inc=1, size=(90, -1)
        )
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        self.rmsd_font_weight_check = make_checkbox(self, "Bold")
        self.rmsd_font_weight_check.SetValue(CONFIG.rmsd_fontWeight)
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_rmsd_label)

        rmsd_color_label = wx.StaticText(self, -1, "Label color:")
        self.rmsd_color_btn = wx.Button(self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsd.label")
        self.rmsd_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_color))
        self.rmsd_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_line_width = wx.StaticText(self, -1, "Line width:")
        self.rmsd_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.lineWidth_1D * 10),
            min=1,
            max=100,
            initial=CONFIG.rmsd_lineWidth * 10,
            inc=5,
            size=(90, -1),
            name="rmsf",
        )
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        rmsd_line_color = wx.StaticText(self, -1, "Line color:")
        self.rmsd_color_line_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsd.line"
        )
        self.rmsd_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_lineColour))
        self.rmsd_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_line_style = wx.StaticText(self, -1, "Line style:")
        self.rmsd_line_style_value = wx.Choice(self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="rmsf")
        self.rmsd_line_style_value.SetStringSelection(CONFIG.rmsd_lineStyle)
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_update)

        rmsd_line_hatch = wx.StaticText(self, -1, "Fill hatch:")
        self.rmsd_line_hatch_value = wx.Choice(
            self, -1, choices=list(CONFIG.lineHatchDict.keys()), size=(-1, -1), name="rmsf"
        )
        self.rmsd_line_hatch_value.SetStringSelection(
            list(CONFIG.lineHatchDict.keys())[list(CONFIG.lineHatchDict.values()).index(CONFIG.rmsd_lineHatch)]
        )
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_update)

        rmsd_underline_color = wx.StaticText(self, -1, "Fill color:")
        self.rmsd_underline_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsd.fill"
        )
        self.rmsd_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_underlineColor))
        self.rmsd_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_alpha_label = wx.StaticText(self, -1, "Fill transparency:")
        self.rmsd_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_underlineTransparency * 100),
            min=0,
            max=100,
            initial=CONFIG.rmsd_underlineTransparency * 100,
            inc=5,
            size=(90, -1),
            name="rmsf",
        )
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        rmsd_hspace_label = wx.StaticText(self, -1, "Vertical spacing:")
        self.rmsd_vspace_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_hspace),
            min=0,
            max=1,
            initial=CONFIG.rmsd_hspace,
            inc=0.05,
            size=(90, -1),
            name="rmsf.spacing",
        )
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)
        set_tooltip(self.rmsd_vspace_value, "Vertical spacing between RMSF and heatmap plot.")

        rmsd_x_rotation = wx.StaticText(self, -1, "Tick rotation (x-axis):")
        self.rmsd_x_rotation_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_rotation_X),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_label_rmsd_matrix)

        rmsd_y_rotation = wx.StaticText(self, -1, "Tick rotation (y-axis):")
        self.rmsd_y_rotation_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_rotation_Y),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_label_rmsd_matrix)

        rmsd_add_labels_label = wx.StaticText(self, -1, "Show RMSD labels:")
        self.rmsd_add_labels_check = make_checkbox(self, "", name="rmsd_matrix")
        self.rmsd_add_labels_check.SetValue(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update_label_rmsd_matrix)

        rmsd_matrix_fontsize = wx.StaticText(self, -1, "Label font size:")
        self.rmsd_matrix_fontsize = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.labelFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.labelFontSize_1D,
            inc=2,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.rmsd_matrix_font_weight_check = make_checkbox(self, "Bold", name="rmsd_matrix")
        self.rmsd_matrix_font_weight_check.SetValue(CONFIG.labelFontWeight_1D)
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        rmsd_matrix_color_fmt = wx.StaticText(self, -1, "Color formatter:")
        self.rmsd_matrix_color_fmt = wx.Choice(
            self, -1, choices=CONFIG.rmsd_matrix_font_color_choices, size=(-1, -1), name="rmsd_matrix_formatter"
        )
        self.rmsd_matrix_color_fmt.SetStringSelection(CONFIG.rmsd_matrix_font_color_choice)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_toggle_controls)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_update)

        rmsd_matrix_font_color = wx.StaticText(self, -1, "Labels color:")
        self.rmsd_matrix_font_color_btn = wx.Button(
            self, -1, "", wx.DefaultPosition, wx.Size(26, 26), name="rmsd.matrix.label"
        )
        self.rmsd_matrix_font_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_matrix_font_color))
        self.rmsd_matrix_font_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # put it all together
        rmsd_parameters_label = wx.StaticText(self, -1, "RMSD parameters")
        set_item_font(rmsd_parameters_label)

        rmsf_parameters_label = wx.StaticText(self, -1, "RMSF parameters")
        set_item_font(rmsf_parameters_label)

        matrix_parameters_label = wx.StaticText(self, -1, "RMSD matrix parameters")
        set_item_font(matrix_parameters_label)

        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        # rmsd controls
        n = 0
        grid.Add(rmsd_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_position_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_x_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_x_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_y_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_y_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_fontsize_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_color_btn, (n, 1), flag=wx.ALIGN_LEFT)

        # rmsf controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_color_line_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(rmsd_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_style_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_hatch, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_hatch_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_underline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_underline_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(rmsd_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_hspace_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_vspace_value, (n, 1), flag=wx.EXPAND)

        # rmsd matrix controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(matrix_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_x_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_x_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_y_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_y_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_add_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_add_labels_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_matrix_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_color_fmt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_color_fmt, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_font_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_font_color_btn, (n, 1), flag=wx.ALIGN_LEFT)

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

        # rmsd
        CONFIG.rmsd_position = self.rmsd_position_value.GetStringSelection()
        CONFIG.rmsd_fontSize = str2num(self.rmsd_fontsize_value.GetValue())
        CONFIG.rmsd_fontWeight = self.rmsd_font_weight_check.GetValue()
        CONFIG.rmsd_rotation_X = str2num(self.rmsd_x_rotation_value.GetValue())
        CONFIG.rmsd_rotation_Y = str2num(self.rmsd_y_rotation_value.GetValue())
        CONFIG.rmsd_lineStyle = self.rmsd_line_style_value.GetStringSelection()
        CONFIG.rmsd_lineHatch = CONFIG.lineHatchDict[self.rmsd_line_hatch_value.GetStringSelection()]
        CONFIG.rmsd_underlineTransparency = str2num(self.rmsd_alpha_value.GetValue()) / 100
        CONFIG.rmsd_hspace = str2num(self.rmsd_vspace_value.GetValue())
        CONFIG.rmsd_lineWidth = self.rmsd_line_width_value.GetValue()

        # rmsd matrix
        CONFIG.rmsd_matrix_add_labels = self.rmsd_add_labels_check.GetValue()
        CONFIG.rmsd_matrix_font_color_choice = self.rmsd_matrix_color_fmt.GetStringSelection()
        CONFIG.rmsd_matrix_font_weight = self.rmsd_matrix_font_weight_check.GetValue()
        CONFIG.rmsd_matrix_font_size = self.rmsd_matrix_fontsize.GetValue()

        if evt is not None:
            evt.Skip()

    def _recalculate_rmsd_position(self, evt):
        if self.import_evt:
            return

        CONFIG.rmsd_position = self.rmsd_position_value.GetStringSelection()
        rmsd_dict = {
            "bottom left": [5, 5],
            "bottom right": [75, 5],
            "top left": [5, 95],
            "top right": [75, 95],
            "none": None,
            "other": [str2int(self.rmsd_x_position_value.GetValue()), str2int(self.rmsd_y_position_value.GetValue())],
        }
        CONFIG.rmsd_location = rmsd_dict[CONFIG.rmsd_position]

        if CONFIG.rmsd_location is not None:
            self.rmsd_x_position_value.SetValue(CONFIG.rmsd_location[0])
            self.rmsd_y_position_value.SetValue(CONFIG.rmsd_location[1])

        self._parse_evt(evt)

    def on_update_rmsd_label(self, evt):
        """Update RMSD label"""
        self.on_apply(None)
        self._recalculate_rmsd_position(None)

        self.panel_plot.plot_2d_update_label()

        self._parse_evt(evt)

    def on_update_label_rmsd_matrix(self, evt):
        """Update RMSD matrix labels"""
        self.on_apply(None)

        self.panel_plot.plot_2D_matrix_update_label()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update RMSD settings"""

        CONFIG.rmsd_position = self.rmsd_position_value.GetStringSelection()
        self.rmsd_x_position_value.Enable(CONFIG.rmsd_position == "other")
        self.rmsd_y_position_value.Enable(CONFIG.rmsd_position == "other")

        CONFIG.rmsd_matrix_font_color_choice = self.rmsd_matrix_color_fmt.GetStringSelection()
        self.rmsd_matrix_font_color_btn.Enable(CONFIG.rmsd_matrix_font_color_choice != "auto")

        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "rmsd.label":
            CONFIG.rmsd_color = color_1
            self.rmsd_color_btn.SetBackgroundColour(color_255)
            self.on_update_rmsd_label(None)
        elif source == "rmsd.line":
            CONFIG.rmsd_lineColour = color_1
            self.rmsd_color_line_btn.SetBackgroundColour(color_255)
            self.panel_plot.plot_1D_update(plotName="RMSF")
        elif source == "rmsd.matrix.label":
            CONFIG.rmsd_matrix_font_color = color_1
            self.rmsd_matrix_font_color_btn.SetBackgroundColour(color_255)
            self.on_update(None)
        elif source == "rmsd.fill":
            CONFIG.rmsd_underlineColor = color_1
            self.rmsd_underline_color_btn.SetBackgroundColour(color_255)
            self.panel_plot.plot_1D_update(plotName="RMSF")
