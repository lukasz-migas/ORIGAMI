"""Legend panel"""
# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelGeneralSettings(PanelSettingsBase):
    """Violin settings"""

    plot_tick_fontsize_value, plot_tick_font_weight_check, plot_label_fontsize_value = None, None, None
    plot_label_font_weight_check, plot_title_fontsize_value, plot1d_title_font_weight_check = None, None, None
    plot_annotation_fontsize_value, plot_annotation_font_weight_check, plot_axis_on_off_check = None, None, None
    plot_left_spines_check, plot_right_spines_check, plot_top_spines_check = None, None, None
    plot_bottom_spines_check, plot_left_ticks_check, plot_right_ticks_check = None, None, None
    plot_top_ticks_check, plot_bottom_ticks_check, plot_left_tick_labels_check = None, None, None
    plot_right_tick_labels_check, plot_top_tick_labels_check, plot_bottom_tick_labels_check = None, None, None
    plot_padding_value, plot_frame_width_value, plot_palette_value, plot_style_value = None, None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """General settings"""

        plot_axis_on_off = wx.StaticText(self, -1, "Show frame:")
        self.plot_axis_on_off_check = make_checkbox(self, "", name="frame")
        self.plot_axis_on_off_check.SetValue(CONFIG.axisOnOff_1D)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        plot_spines = wx.StaticText(self, -1, "Line:")
        self.plot_left_spines_check = make_checkbox(self, "Left", name="frame")
        self.plot_left_spines_check.SetValue(CONFIG.spines_left_1D)
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_spines_check = make_checkbox(self, "Right", name="frame")
        self.plot_right_spines_check.SetValue(CONFIG.spines_right_1D)
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_spines_check = make_checkbox(self, "Top", name="frame")
        self.plot_top_spines_check.SetValue(CONFIG.spines_top_1D)
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_spines_check = make_checkbox(self, "Bottom", name="frame")
        self.plot_bottom_spines_check.SetValue(CONFIG.spines_bottom_1D)
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_ticks_label = wx.StaticText(self, -1, "Ticks:")
        self.plot_left_ticks_check = make_checkbox(self, "Left", name="frame")
        self.plot_left_ticks_check.SetValue(CONFIG.ticks_left_1D)
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_ticks_check = make_checkbox(self, "Right", name="frame")
        self.plot_right_ticks_check.SetValue(CONFIG.ticks_right_1D)
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_ticks_check = make_checkbox(self, "Top", name="frame")
        self.plot_top_ticks_check.SetValue(CONFIG.ticks_top_1D)
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_ticks_check = make_checkbox(self, "Bottom", name="frame")
        self.plot_bottom_ticks_check.SetValue(CONFIG.ticks_bottom_1D)
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_labels = wx.StaticText(self, -1, "Tick labels:")
        self.plot_left_tick_labels_check = make_checkbox(self, "Left", name="frame")
        self.plot_left_tick_labels_check.SetValue(CONFIG.tickLabels_left_1D)
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_tick_labels_check = make_checkbox(self, "Right", name="frame")
        self.plot_right_tick_labels_check.SetValue(CONFIG.tickLabels_right_1D)
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_tick_labels_check = make_checkbox(self, "Top", name="frame")
        self.plot_top_tick_labels_check.SetValue(CONFIG.tickLabels_top_1D)
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_tick_labels_check = make_checkbox(self, "Bottom", name="frame")
        self.plot_bottom_tick_labels_check.SetValue(CONFIG.tickLabels_bottom_1D)
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_frame_width = wx.StaticText(self, -1, "Frame width:")
        self.plot_frame_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.frameWidth_1D),
            min=0,
            max=10,
            initial=CONFIG.frameWidth_1D,
            inc=1,
            size=(90, -1),
            name="frame",
        )
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_padding = wx.StaticText(self, -1, "Label pad:")
        self.plot_padding_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.labelPad_1D),
            min=0,
            max=100,
            initial=CONFIG.labelPad_1D,
            inc=5,
            size=(90, -1),
            name="fonts",
        )
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_title_fontsize = wx.StaticText(self, -1, "Title font size:")
        self.plot_title_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.titleFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.titleFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot1d_title_font_weight_check = make_checkbox(self, "Bold", name="fonts")
        self.plot1d_title_font_weight_check.SetValue(CONFIG.titleFontWeight_1D)
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_label_fontsize = wx.StaticText(self, -1, "Label font size:")
        self.plot_label_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.labelFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.labelFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_label_font_weight_check = make_checkbox(self, "Bold", name="fonts")
        self.plot_label_font_weight_check.SetValue(CONFIG.labelFontWeight_1D)
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_fontsize = wx.StaticText(self, -1, "Tick font size:")
        self.plot_tick_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.tickFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.tickFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_tick_font_weight_check = make_checkbox(self, "Bold", name="fonts")
        self.plot_tick_font_weight_check.SetValue(CONFIG.tickFontWeight_1D)
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_tick_font_weight_check.Disable()

        plot_annotation_fontsize = wx.StaticText(self, -1, "Annotation font size:")
        self.plot_annotation_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.annotationFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.annotationFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_annotation_font_weight_check = make_checkbox(self, "Bold", name="fonts")
        self.plot_annotation_font_weight_check.SetValue(CONFIG.annotationFontWeight_1D)
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        style_label = wx.StaticText(self, -1, "Style:")
        self.plot_style_value = wx.Choice(self, -1, choices=CONFIG.styles, size=(-1, -1))
        self.plot_style_value.SetStringSelection(CONFIG.currentStyle)
        self.plot_style_value.Bind(wx.EVT_CHOICE, self.on_change_plot_style)

        plot_palette = wx.StaticText(self, -1, "Color palette:")
        self.plot_palette_value = BitmapComboBox(self, -1, choices=[], size=(160, -1), style=wx.CB_READONLY)
        self._set_color_palette(self.plot_palette_value)
        self.plot_palette_value.SetStringSelection(CONFIG.currentPalette)
        self.plot_palette_value.Bind(wx.EVT_COMBOBOX, self.on_change_color_palette)

        axis_parameters_label = wx.StaticText(self, -1, "Axis and frame parameters")
        set_item_font(axis_parameters_label)

        font_parameters_label = wx.StaticText(self, -1, "Font and label parameters")
        set_item_font(font_parameters_label)

        style_parameters_label = wx.StaticText(self, -1, "Style parameters")
        set_item_font(style_parameters_label)

        # axes parameters
        n_span = 3
        n_col = 5
        grid = wx.GridBagSizer(2, 2)
        # frame controls
        n = 0
        grid.Add(axis_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_axis_on_off, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_axis_on_off_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_spines, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_left_spines_check, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_right_spines_check, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_top_spines_check, (n, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_bottom_spines_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_ticks_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_left_ticks_check, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_right_ticks_check, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_top_ticks_check, (n, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_bottom_ticks_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_tick_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_left_tick_labels_check, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_right_tick_labels_check, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_top_tick_labels_check, (n, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.plot_bottom_tick_labels_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_frame_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_frame_width_value, (n, 1), (1, n_span), flag=wx.EXPAND)
        # label controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(font_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_padding, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_padding_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_title_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_title_fontsize_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        grid.Add(self.plot1d_title_font_weight_check, (n, n_span + 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_label_fontsize_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        grid.Add(self.plot_label_font_weight_check, (n, n_span + 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_tick_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_tick_fontsize_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        grid.Add(self.plot_tick_font_weight_check, (n, n_span + 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_annotation_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_annotation_fontsize_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        grid.Add(self.plot_annotation_font_weight_check, (n, n_span + 1), flag=wx.EXPAND)
        # style controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(style_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(style_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_style_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_palette, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_palette_value, (n, 1), wx.GBSpan(1, n_span), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Update general parameters"""
        CONFIG.tickFontSize_1D = str2num(self.plot_tick_fontsize_value.GetValue())
        CONFIG.tickFontWeight_1D = self.plot_tick_font_weight_check.GetValue()
        CONFIG.labelFontSize_1D = str2num(self.plot_label_fontsize_value.GetValue())
        CONFIG.labelFontWeight_1D = self.plot_label_font_weight_check.GetValue()
        CONFIG.titleFontSize_1D = str2num(self.plot_title_fontsize_value.GetValue())
        CONFIG.titleFontWeight_1D = self.plot1d_title_font_weight_check.GetValue()
        CONFIG.annotationFontSize_1D = str2num(self.plot_annotation_fontsize_value.GetValue())
        CONFIG.annotationFontWeight_1D = self.plot_annotation_font_weight_check.GetValue()
        CONFIG.axisOnOff_1D = self.plot_axis_on_off_check.GetValue()
        CONFIG.spines_left_1D = self.plot_left_spines_check.GetValue()
        CONFIG.spines_right_1D = self.plot_right_spines_check.GetValue()
        CONFIG.spines_top_1D = self.plot_top_spines_check.GetValue()
        CONFIG.spines_bottom_1D = self.plot_bottom_spines_check.GetValue()
        CONFIG.ticks_left_1D = self.plot_left_ticks_check.GetValue()
        CONFIG.ticks_right_1D = self.plot_right_ticks_check.GetValue()
        CONFIG.ticks_top_1D = self.plot_top_ticks_check.GetValue()
        CONFIG.ticks_bottom_1D = self.plot_bottom_ticks_check.GetValue()
        CONFIG.tickLabels_left_1D = self.plot_left_tick_labels_check.GetValue()
        CONFIG.tickLabels_right_1D = self.plot_right_tick_labels_check.GetValue()
        CONFIG.tickLabels_top_1D = self.plot_top_tick_labels_check.GetValue()
        CONFIG.tickLabels_bottom_1D = self.plot_bottom_tick_labels_check.GetValue()
        CONFIG.labelPad_1D = self.plot_padding_value.GetValue()
        CONFIG.frameWidth_1D = self.plot_frame_width_value.GetValue()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update general controls"""
        CONFIG.axisOnOff_1D = self.plot_axis_on_off_check.GetValue()
        self.plot_right_spines_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_top_spines_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_left_spines_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_bottom_spines_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_left_ticks_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_right_ticks_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_top_ticks_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_bottom_ticks_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_left_tick_labels_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_right_tick_labels_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_top_tick_labels_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_bottom_tick_labels_check.Enable(CONFIG.axisOnOff_1D)
        self.plot_frame_width_value.Enable(CONFIG.axisOnOff_1D)

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update"""
        self._parse_evt(evt)

    def on_change_plot_style(self, evt):
        """Change plot sizes"""
        if self.import_evt:
            return

        CONFIG.currentStyle = self.plot_style_value.GetStringSelection()
        self.panel_plot.on_change_plot_style()

        self._parse_evt(evt)

    def on_change_color_palette(self, evt):
        """Update color palette"""
        if self.import_evt:
            return

        CONFIG.currentPalette = self.plot_palette_value.GetStringSelection()
        self.panel_plot.on_change_color_palette(evt=None)

        self._parse_evt(evt)
