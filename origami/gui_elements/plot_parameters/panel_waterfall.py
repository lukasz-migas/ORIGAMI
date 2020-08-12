"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelWaterfallSettings(PanelSettingsBase):
    """Violin settings"""

    waterfall_label_format_value = None
    waterfall_fill_n_limit_value, waterfall_fill_transparency_value, waterfall_fill_under_check = None, None, None
    waterfall_label_font_weight_check, waterfall_label_font_size_value = None, None
    waterfall_increment_value, waterfall_line_width_value, waterfall_line_style_value = None, None, None
    waterfall_reverse_check, waterfall_colorScheme_value = None, None
    waterfall_label_x_offset_value, waterfall_label_frequency_value, waterfall_showLabels_check = None, None, None
    waterfall_line_sameAsShade_check, waterfall_normalize_check, waterfall_colormap_value = None, None, None
    waterfall_palette_value, waterfall_color_fill_btn, waterfall_color_line_btn = None, None, None
    waterfall_label_y_offset_value = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make waterfall panel"""
        waterfall_increment_label = wx.StaticText(self, -1, "Increment:")
        self.waterfall_increment_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_increment),
            min=0.0,
            max=99999.0,
            initial=0,
            inc=0.1,
            size=(90, -1),
            name="waterfall.data",
        )
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        waterfall_normalize_label = wx.StaticText(self, -1, "Normalize:")
        self.waterfall_normalize_check = make_checkbox(self, "", name="waterfall.data")
        self.waterfall_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.waterfall_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.waterfall_normalize_check.SetToolTip(
            "Controls whether signals are normalized during plotting. Changing this value will not have immediate"
            " effect until the plot is fully replotted."
        )

        waterfall_reverse_label = wx.StaticText(self, -1, "Reverse order:")
        self.waterfall_reverse_check = make_checkbox(self, "", name="waterfall.data")
        self.waterfall_reverse_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.waterfall_reverse_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.waterfall_reverse_check.SetToolTip(
            "Controls in which order lines are plotted. Changing this value will not have immediate"
            " effect until the plot is fully replotted."
        )

        # line style
        waterfall_line_width_label = wx.StaticText(self, -1, "Line width:")
        self.waterfall_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_line_width),
            min=1,
            max=10,
            initial=CONFIG.waterfall_line_width,
            inc=1,
            size=(90, -1),
            name="waterfall.line",
        )
        self.waterfall_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        waterfall_line_style_label = wx.StaticText(self, -1, "Line style:")
        self.waterfall_line_style_value = wx.Choice(
            self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="waterfall.line"
        )
        self.waterfall_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.waterfall_line_style_value.Bind(wx.EVT_CHOICE, self.on_update)

        waterfall_line_color_label = wx.StaticText(self, -1, "Line color:")
        self.waterfall_color_line_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="waterfall.line.color"
        )
        self.waterfall_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.waterfall_line_sameAsShade_check = make_checkbox(self, "Same as fill", name="waterfall.fill")
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        # under-line style
        waterfall_shade_under_label = wx.StaticText(self, -1, "Fill under the curve:")
        self.waterfall_fill_under_check = make_checkbox(self, "", name="waterfall.fill")
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        waterfall_color_scheme_label = wx.StaticText(self, -1, "Color scheme:")
        self.waterfall_colorScheme_value = wx.Choice(
            self, -1, choices=CONFIG.waterfall_color_choices, size=(-1, -1), name="waterfall.fill"
        )
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        cmap_list = CONFIG.colormap_choices[:]
        cmap_list.remove("jet")
        waterfall_colormap_label = wx.StaticText(self, -1, "Colormap:")
        self.waterfall_colormap_value = wx.Choice(self, -1, choices=cmap_list, size=(-1, -1), name="waterfall.fill")
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.on_update)

        waterfall_palette = wx.StaticText(self, -1, "Color palette:")
        self.waterfall_palette_value = BitmapComboBox(self, -1, choices=[], size=(160, -1), style=wx.CB_READONLY)
        self._set_color_palette(self.waterfall_palette_value)
        self.waterfall_palette_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.waterfall_palette_value.Bind(wx.EVT_COMBOBOX, self.on_update)

        waterfall_shade_color_label = wx.StaticText(self, -1, "Fill color:")
        self.waterfall_color_fill_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="waterfall.fill.color"
        )
        self.waterfall_color_fill_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        waterfall_shade_transparency_label = wx.StaticText(self, -1, "Fill transparency:")
        self.waterfall_fill_transparency_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_fill_under_transparency),
            min=0,
            max=1,
            initial=CONFIG.waterfall_fill_under_transparency,
            inc=0.25,
            size=(90, -1),
            name="waterfall.fill",
        )
        self.waterfall_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        waterfall_shade_limit_label = wx.StaticText(self, -1, "Fill limit:")
        self.waterfall_fill_n_limit_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_fill_under_nlimit),
            min=0,
            max=1500,
            initial=CONFIG.waterfall_fill_under_nlimit,
            inc=100,
            size=(90, -1),
            name="waterfall.fill",
        )
        self.waterfall_fill_n_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_fill_n_limit_value.SetToolTip(
            "Maximum number of items to be considered for fill-in plotting. If the number is very high, plotting"
            + " can be slow"
        )

        waterfall_show_labels_label = wx.StaticText(self, -1, "Show labels:")
        self.waterfall_showLabels_check = make_checkbox(self, "", name="waterfall.label.reset")
        self.waterfall_showLabels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.waterfall_showLabels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        waterfall_label_frequency_label = wx.StaticText(self, -1, "Label frequency:")
        self.waterfall_label_frequency_value = wx.SpinCtrl(
            self,
            -1,
            value=str(CONFIG.waterfall_labels_frequency),
            min=0,
            max=100,
            initial=CONFIG.waterfall_labels_frequency,
            size=(45, -1),
            name="waterfall.label.reset",
        )
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        waterfall_label_format_label = wx.StaticText(self, -1, "Label format:")
        self.waterfall_label_format_value = wx.Choice(
            self, -1, choices=CONFIG.waterfall_labels_format_choices, size=(-1, -1), name="waterfall.label.reset"
        )
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        waterfall_label_font_size_label = wx.StaticText(self, -1, "Font size:")
        self.waterfall_label_font_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_labels_font_size),
            min=4,
            max=32,
            initial=CONFIG.waterfall_labels_font_size,
            inc=2,
            size=(45, -1),
            name="waterfall.label",
        )
        self.waterfall_label_font_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_label_font_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.waterfall_label_font_weight_check = make_checkbox(self, "Bold", name="waterfall.label")
        self.waterfall_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.waterfall_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        waterfall_label_x_offset_label = wx.StaticText(self, -1, "Horizontal offset:")
        self.waterfall_label_x_offset_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_labels_x_offset),
            min=0,
            max=1,
            initial=CONFIG.waterfall_labels_x_offset,
            inc=0.01,
            size=(45, -1),
            name="waterfall.label.reset",
        )
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        waterfall_label_y_offset_label = wx.StaticText(self, -1, "Vertical offset:")
        self.waterfall_label_y_offset_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.waterfall_labels_y_offset),
            min=0,
            max=1,
            initial=CONFIG.waterfall_labels_y_offset,
            inc=0.05,
            size=(45, -1),
            name="waterfall.label.reset",
        )
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_parameters_label = wx.StaticText(self, -1, "Plot parameters")
        set_item_font(plot_parameters_label)

        labels_parameters_label = wx.StaticText(self, -1, "Labels parameters")
        set_item_font(labels_parameters_label)

        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        # waterfall controls
        n = 0
        grid.Add(plot_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_increment_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_increment_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_normalize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_normalize_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_reverse_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_reverse_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_line_style_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_line_style_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_line_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_line_sameAsShade_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.waterfall_color_line_btn, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(waterfall_shade_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_fill_under_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_color_scheme_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colorScheme_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colormap_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_palette, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_palette_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_shade_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_color_fill_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(waterfall_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_fill_transparency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_shade_limit_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_fill_n_limit_value, (n, 1), flag=wx.EXPAND)
        # label controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(labels_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_show_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_showLabels_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_label_frequency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_frequency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_label_format_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_format_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_label_font_size_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_font_size_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.waterfall_label_font_weight_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(waterfall_label_x_offset_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_x_offset_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(waterfall_label_y_offset_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_y_offset_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply waterfall settings"""
        if self.import_evt:
            return
        CONFIG.waterfall_increment = self.waterfall_increment_value.GetValue()
        CONFIG.waterfall_line_width = self.waterfall_line_width_value.GetValue()
        CONFIG.waterfall_line_style = self.waterfall_line_style_value.GetStringSelection()
        CONFIG.waterfall_reverse = self.waterfall_reverse_check.GetValue()
        CONFIG.waterfall_color_scheme = self.waterfall_colorScheme_value.GetStringSelection()
        CONFIG.waterfall_palette = self.waterfall_palette_value.GetStringSelection()
        CONFIG.waterfall_colormap = self.waterfall_colormap_value.GetStringSelection()
        CONFIG.waterfall_normalize = self.waterfall_normalize_check.GetValue()
        CONFIG.waterfall_line_same_as_fill = self.waterfall_line_sameAsShade_check.GetValue()
        CONFIG.waterfall_labels_show = self.waterfall_showLabels_check.GetValue()
        CONFIG.waterfall_labels_frequency = int(self.waterfall_label_frequency_value.GetValue())
        CONFIG.waterfall_labels_x_offset = self.waterfall_label_x_offset_value.GetValue()
        CONFIG.waterfall_labels_y_offset = self.waterfall_label_y_offset_value.GetValue()
        CONFIG.waterfall_labels_font_size = self.waterfall_label_font_size_value.GetValue()
        CONFIG.waterfall_labels_font_weight = self.waterfall_label_font_weight_check.GetValue()
        CONFIG.waterfall_fill_under = self.waterfall_fill_under_check.GetValue()
        CONFIG.waterfall_fill_under_transparency = self.waterfall_fill_transparency_value.GetValue()
        CONFIG.waterfall_fill_under_nlimit = self.waterfall_fill_n_limit_value.GetValue()
        CONFIG.waterfall_labels_format = self.waterfall_label_format_value.GetStringSelection()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update waterfall controls"""
        CONFIG.waterfall_line_same_as_fill = self.waterfall_line_sameAsShade_check.GetValue()
        self.waterfall_color_line_btn.Enable(not CONFIG.waterfall_line_same_as_fill)

        # update patch coloring
        CONFIG.waterfall_fill_under = self.waterfall_fill_under_check.GetValue()
        self.waterfall_fill_transparency_value.Enable(CONFIG.waterfall_fill_under)
        self.waterfall_fill_n_limit_value.Enable(CONFIG.waterfall_fill_under)

        # update labels
        CONFIG.waterfall_labels_show = self.waterfall_showLabels_check.GetValue()
        self.waterfall_label_format_value.Enable(CONFIG.waterfall_labels_show)
        self.waterfall_label_font_size_value.Enable(CONFIG.waterfall_labels_show)
        self.waterfall_label_font_weight_check.Enable(CONFIG.waterfall_labels_show)
        self.waterfall_label_frequency_value.Enable(CONFIG.waterfall_labels_show)
        self.waterfall_label_x_offset_value.Enable(CONFIG.waterfall_labels_show)
        self.waterfall_label_y_offset_value.Enable(CONFIG.waterfall_labels_show)

        CONFIG.waterfall_color_scheme = self.waterfall_colorScheme_value.GetStringSelection()
        self.waterfall_color_fill_btn.Enable(CONFIG.waterfall_color_scheme == "Same color")
        self.waterfall_colormap_value.Enable(CONFIG.waterfall_color_scheme == "Colormap")
        self.waterfall_palette_value.Enable(CONFIG.waterfall_color_scheme == "Color palette")

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update waterfall plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return

        if not source.startswith("waterfall."):
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

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "waterfall.line.color":
            CONFIG.waterfall_line_color = color_1
            self.waterfall_color_line_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "waterfall.fill.color":
            CONFIG.waterfall_fill_under_color = color_1
            self.waterfall_color_fill_btn.SetBackgroundColour(color_255)
            self.on_update(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.waterfall_increment_value.SetValue(CONFIG.waterfall_increment)
        self.waterfall_normalize_check.SetValue(CONFIG.waterfall_normalize)
        self.waterfall_reverse_check.SetValue(CONFIG.waterfall_reverse)
        self.waterfall_line_width_value.SetValue(CONFIG.waterfall_line_width)
        self.waterfall_line_style_value.SetStringSelection(CONFIG.waterfall_line_style)
        self.waterfall_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.waterfall_line_color))
        self.waterfall_line_sameAsShade_check.SetValue(CONFIG.waterfall_line_same_as_fill)
        self.waterfall_fill_under_check.SetValue(CONFIG.waterfall_fill_under)
        self.waterfall_colorScheme_value.SetStringSelection(CONFIG.waterfall_color_scheme)
        self.waterfall_colormap_value.SetStringSelection(CONFIG.waterfall_colormap)
        self.waterfall_palette_value.SetStringSelection(CONFIG.waterfall_palette)
        self.waterfall_color_fill_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.waterfall_fill_under_color))
        self.waterfall_fill_transparency_value.SetValue(CONFIG.waterfall_fill_under_transparency)
        self.waterfall_fill_n_limit_value.SetValue(CONFIG.waterfall_fill_under_nlimit)
        self.waterfall_showLabels_check.SetValue(CONFIG.waterfall_labels_show)
        self.waterfall_label_frequency_value.SetValue(CONFIG.waterfall_labels_frequency)
        self.waterfall_label_format_value.SetStringSelection(CONFIG.waterfall_labels_format)
        self.waterfall_label_font_size_value.SetValue(CONFIG.waterfall_labels_font_size)
        self.waterfall_label_font_weight_check.SetValue(CONFIG.waterfall_labels_font_weight)
        self.waterfall_label_y_offset_value.SetValue(CONFIG.waterfall_labels_y_offset)
        self.import_evt = False
