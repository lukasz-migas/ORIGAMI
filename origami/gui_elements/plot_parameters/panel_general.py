"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


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
        self.plot_axis_on_off_check = make_checkbox(self, "", name="axes.frame")
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        plot_spines = wx.StaticText(self, -1, "Line:")
        self.plot_left_spines_check = make_checkbox(self, "Left", name="axes.frame")
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_spines_check = make_checkbox(self, "Right", name="axes.frame")
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_spines_check = make_checkbox(self, "Top", name="axes.frame")
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_spines_check = make_checkbox(self, "Bottom", name="axes.frame")
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_ticks_label = wx.StaticText(self, -1, "Ticks:")
        self.plot_left_ticks_check = make_checkbox(self, "Left", name="axes.frame")
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_ticks_check = make_checkbox(self, "Right", name="axes.frame")
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_ticks_check = make_checkbox(self, "Top", name="axes.frame")
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_ticks_check = make_checkbox(self, "Bottom", name="axes.frame")
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_labels = wx.StaticText(self, -1, "Tick labels:")
        self.plot_left_tick_labels_check = make_checkbox(self, "Left", name="axes.frame")
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_tick_labels_check = make_checkbox(self, "Right", name="axes.frame")
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_tick_labels_check = make_checkbox(self, "Top", name="axes.frame")
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_tick_labels_check = make_checkbox(self, "Bottom", name="axes.frame")
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_frame_width = wx.StaticText(self, -1, "Frame width:")
        self.plot_frame_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_frame_width),
            min=0,
            max=10,
            initial=CONFIG.axes_frame_width,
            inc=1,
            size=(90, -1),
            name="axes.frame",
        )
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_padding = wx.StaticText(self, -1, "Label pad:")
        self.plot_padding_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_label_pad),
            min=0,
            max=100,
            initial=CONFIG.axes_label_pad,
            inc=5,
            size=(90, -1),
            name="axes.labels",
        )
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_title_fontsize = wx.StaticText(self, -1, "Title font size:")
        self.plot_title_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_title_font_size),
            min=0,
            max=48,
            initial=CONFIG.axes_title_font_size,
            inc=2,
            size=(90, -1),
            name="axes.labels",
        )
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot1d_title_font_weight_check = make_checkbox(self, "Bold", name="axes.labels")
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_label_fontsize = wx.StaticText(self, -1, "Label font size:")
        self.plot_label_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_label_font_size),
            min=0,
            max=48,
            initial=CONFIG.axes_label_font_size,
            inc=2,
            size=(90, -1),
            name="axes.labels",
        )
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_label_font_weight_check = make_checkbox(self, "Bold", name="axes.labels")
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_fontsize = wx.StaticText(self, -1, "Tick font size:")
        self.plot_tick_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_tick_font_size),
            min=0,
            max=48,
            initial=CONFIG.axes_tick_font_size,
            inc=2,
            size=(90, -1),
            name="axes.frame",
        )
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_tick_font_weight_check = make_checkbox(self, "Bold", name="axes.labels")
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_tick_font_weight_check.Disable()

        plot_annotation_fontsize = wx.StaticText(self, -1, "Annotation font size:")
        self.plot_annotation_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_annotation_font_size),
            min=0,
            max=48,
            initial=CONFIG.axes_annotation_font_size,
            inc=2,
            size=(90, -1),
            name="axes.labels",
        )
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_annotation_font_weight_check = make_checkbox(self, "Bold", name="axes.labels")
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        style_label = wx.StaticText(self, -1, "Style:")
        self.plot_style_value = wx.Choice(self, -1, choices=CONFIG.plot_style_choices, size=(-1, -1))
        self.plot_style_value.Bind(wx.EVT_CHOICE, self.on_change_plot_style)

        plot_palette = wx.StaticText(self, -1, "Color palette:")
        self.plot_palette_value = BitmapComboBox(self, -1, choices=[], size=(160, -1), style=wx.CB_READONLY)
        self._set_color_palette(self.plot_palette_value)
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
        if self.import_evt:
            return
        CONFIG.axes_tick_font_size = str2num(self.plot_tick_fontsize_value.GetValue())
        CONFIG.axes_tick_font_weight = self.plot_tick_font_weight_check.GetValue()
        CONFIG.axes_label_font_size = str2num(self.plot_label_fontsize_value.GetValue())
        CONFIG.axes_label_font_weight = self.plot_label_font_weight_check.GetValue()
        CONFIG.axes_title_font_size = str2num(self.plot_title_fontsize_value.GetValue())
        CONFIG.axes_title_font_weight = self.plot1d_title_font_weight_check.GetValue()
        CONFIG.axes_annotation_font_size = str2num(self.plot_annotation_fontsize_value.GetValue())
        CONFIG.axes_annotation_font_weight = self.plot_annotation_font_weight_check.GetValue()
        CONFIG.axes_frame_show = self.plot_axis_on_off_check.GetValue()
        CONFIG.axes_frame_spine_left = self.plot_left_spines_check.GetValue()
        CONFIG.axes_frame_spine_right = self.plot_right_spines_check.GetValue()
        CONFIG.axes_frame_spine_top = self.plot_top_spines_check.GetValue()
        CONFIG.axes_frame_spine_bottom = self.plot_bottom_spines_check.GetValue()
        CONFIG.axes_frame_ticks_left = self.plot_left_ticks_check.GetValue()
        CONFIG.axes_frame_ticks_right = self.plot_right_ticks_check.GetValue()
        CONFIG.axes_frame_ticks_top = self.plot_top_ticks_check.GetValue()
        CONFIG.axes_frame_ticks_bottom = self.plot_bottom_ticks_check.GetValue()
        CONFIG.axes_frame_tick_labels_left = self.plot_left_tick_labels_check.GetValue()
        CONFIG.axes_frame_tick_labels_right = self.plot_right_tick_labels_check.GetValue()
        CONFIG.axes_frame_tick_labels_top = self.plot_top_tick_labels_check.GetValue()
        CONFIG.axes_frame_tick_labels_bottom = self.plot_bottom_tick_labels_check.GetValue()
        CONFIG.axes_label_pad = self.plot_padding_value.GetValue()
        CONFIG.axes_frame_width = self.plot_frame_width_value.GetValue()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update general controls"""
        CONFIG.axes_frame_show = self.plot_axis_on_off_check.GetValue()
        self.plot_right_spines_check.Enable(CONFIG.axes_frame_show)
        self.plot_top_spines_check.Enable(CONFIG.axes_frame_show)
        self.plot_left_spines_check.Enable(CONFIG.axes_frame_show)
        self.plot_bottom_spines_check.Enable(CONFIG.axes_frame_show)
        self.plot_left_ticks_check.Enable(CONFIG.axes_frame_show)
        self.plot_right_ticks_check.Enable(CONFIG.axes_frame_show)
        self.plot_top_ticks_check.Enable(CONFIG.axes_frame_show)
        self.plot_bottom_ticks_check.Enable(CONFIG.axes_frame_show)
        self.plot_left_tick_labels_check.Enable(CONFIG.axes_frame_show)
        self.plot_right_tick_labels_check.Enable(CONFIG.axes_frame_show)
        self.plot_top_tick_labels_check.Enable(CONFIG.axes_frame_show)
        self.plot_bottom_tick_labels_check.Enable(CONFIG.axes_frame_show)
        self.plot_frame_width_value.Enable(CONFIG.axes_frame_show)

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("axes."):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source
        try:
            view = VIEW_REG.view
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_change_plot_style(self, evt):
        """Change plot sizes"""
        if self.import_evt:
            return

        CONFIG.current_style = self.plot_style_value.GetStringSelection()
        self.panel_plot.on_change_plot_style()
        try:
            view = VIEW_REG.view
            view.replot(light_clear=True)
        except (AttributeError, KeyError):
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_change_color_palette(self, evt):
        """Update color palette"""
        if self.import_evt:
            return

        CONFIG.current_palette = self.plot_palette_value.GetStringSelection()
        self.panel_plot.on_change_color_palette(evt=None)
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        # axes parameters
        self.plot_axis_on_off_check.SetValue(CONFIG.axes_frame_show)
        self.plot_left_spines_check.SetValue(CONFIG.axes_frame_spine_left)
        self.plot_right_spines_check.SetValue(CONFIG.axes_frame_spine_right)
        self.plot_top_spines_check.SetValue(CONFIG.axes_frame_spine_top)
        self.plot_bottom_spines_check.SetValue(CONFIG.axes_frame_spine_bottom)
        self.plot_left_ticks_check.SetValue(CONFIG.axes_frame_ticks_left)
        self.plot_right_ticks_check.SetValue(CONFIG.axes_frame_ticks_right)
        self.plot_top_ticks_check.SetValue(CONFIG.axes_frame_ticks_top)
        self.plot_bottom_ticks_check.SetValue(CONFIG.axes_frame_ticks_bottom)
        self.plot_left_tick_labels_check.SetValue(CONFIG.axes_frame_tick_labels_left)
        self.plot_right_tick_labels_check.SetValue(CONFIG.axes_frame_tick_labels_right)
        self.plot_top_tick_labels_check.SetValue(CONFIG.axes_frame_tick_labels_top)
        self.plot_bottom_tick_labels_check.SetValue(CONFIG.axes_frame_tick_labels_bottom)

        # label parameters
        self.plot_padding_value.SetValue(CONFIG.axes_label_pad)
        self.plot_title_fontsize_value.SetValue(CONFIG.axes_title_font_size)
        self.plot1d_title_font_weight_check.SetValue(CONFIG.axes_title_font_weight)
        self.plot_label_fontsize_value.SetValue(CONFIG.axes_label_font_size)
        self.plot_label_font_weight_check.SetValue(CONFIG.axes_label_font_weight)
        self.plot_tick_fontsize_value.SetValue(CONFIG.axes_tick_font_size)
        self.plot_tick_font_weight_check.SetValue(CONFIG.axes_tick_font_weight)
        self.plot_annotation_fontsize_value.SetValue(CONFIG.axes_annotation_font_size)
        self.plot_annotation_font_weight_check.SetValue(CONFIG.axes_annotation_font_weight)

        # style parameters
        self.plot_style_value.SetStringSelection(CONFIG.current_style)
        self.plot_palette_value.SetStringSelection(CONFIG.current_palette)
        self.import_evt = False
