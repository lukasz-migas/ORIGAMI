"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelViolinSettings(PanelSettingsBase):
    """Violin settings"""

    violin_label_format_value, violin_color_line_btn, violin_color_fill_btn = None, None, None
    violin_orientation_value, violin_min_percentage_value, violin_spacing_value = None, None, None
    violin_line_width_value, violin_line_style_value, violin_colorScheme_value = None, None, None
    violin_colormap_value, violin_normalize_check, violin_palette_value = None, None, None
    violin_line_same_as_fill_check, violin_fill_transparency_value, violin_n_limit_value = None, None, None
    violin_smooth_value, violin_smooth_sigma_value, violin_label_frequency_value = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make UI"""
        violin_n_limit_label = wx.StaticText(self, -1, "Violin limit:")
        self.violin_n_limit_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_n_limit),
            min=1,
            max=200,
            initial=CONFIG.violin_n_limit,
            inc=5,
            size=(90, -1),
            name="violin.data",
        )
        self.violin_n_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_n_limit_value.SetToolTip("Maximum number of signals before we plot the data as a waterfall plot.")
        self.violin_n_limit_value.Disable()

        violin_orientation_label = wx.StaticText(self, -1, "Violin plot orientation:")
        self.violin_orientation_value = wx.Choice(
            self, -1, choices=CONFIG.violin_orientation_choices, size=(-1, -1), name="violin.data"
        )
        self.violin_orientation_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.violin_orientation_value.Bind(wx.EVT_CHOICE, self.on_update)

        violin_spacing_label = wx.StaticText(self, -1, "Spacing:")
        self.violin_spacing_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_spacing),
            min=0.0,
            max=5,
            initial=0,
            inc=0.25,
            size=(90, -1),
            name="violin.data",
        )
        self.violin_spacing_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_spacing_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        violin_min_percentage_label = wx.StaticText(self, -1, "Noise threshold:")
        self.violin_min_percentage_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_min_percentage),
            min=0.0,
            max=1.0,
            initial=0,
            inc=0.01,
            size=(90, -1),
            name="violin.data",
        )
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)
        self.violin_min_percentage_value.SetToolTip(
            "Minimal intensity of data to be shown on the plot. Low intensity or sparse datasets can lead"
            " to plot distortions"
        )

        violin_normalize_label = wx.StaticText(self, -1, "Normalize:")
        self.violin_normalize_check = make_checkbox(self, "", name="violin.data")
        self.violin_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.violin_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        violin_smooth_label = wx.StaticText(self, -1, "Smooth:")
        self.violin_smooth_value = make_checkbox(self, "", name="violin.data")
        self.violin_smooth_value.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.violin_smooth_value.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.violin_smooth_value.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        violin_smooth_sigma = wx.StaticText(self, -1, "Gaussian smooth:")
        self.violin_smooth_sigma_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_smooth_sigma),
            min=1,
            max=10,
            initial=CONFIG.violin_smooth_sigma,
            inc=0.5,
            size=(90, -1),
            name="violin.data",
        )
        self.violin_smooth_sigma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_smooth_sigma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        violin_line_width = wx.StaticText(self, -1, "Line width:")
        self.violin_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_line_width),
            min=1,
            max=10,
            initial=CONFIG.violin_line_width,
            inc=1,
            size=(90, -1),
            name="violin.line.style",
        )
        self.violin_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        violin_line_style = wx.StaticText(self, -1, "Line style:")
        self.violin_line_style_value = wx.Choice(
            self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="violin.line"
        )
        self.violin_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.violin_line_style_value.Bind(wx.EVT_CHOICE, self.on_update)

        violin_line_color = wx.StaticText(self, -1, "Line color:")
        self.violin_color_line_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="violin.line.color"
        )
        self.violin_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.violin_line_same_as_fill_check = make_checkbox(self, "Same as fill", name="violin.line")
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        violin_color_scheme_label = wx.StaticText(self, -1, "Color scheme:")
        self.violin_colorScheme_value = wx.Choice(
            self, -1, choices=CONFIG.waterfall_color_scheme_choices, size=(-1, -1), name="violin.fill"
        )
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        cmap_list = CONFIG.colormap_choices[:]
        cmap_list.remove("jet")
        violin_colormap_label = wx.StaticText(self, -1, "Colormap:")
        self.violin_colormap_value = wx.Choice(self, -1, choices=cmap_list, size=(-1, -1), name="violin.fill")
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.on_update)

        violin_palette = wx.StaticText(self, -1, "Color palette:")
        self.violin_palette_value = BitmapComboBox(
            self, -1, choices=[], size=(160, -1), style=wx.CB_READONLY, name="violin.fill"
        )
        self._set_color_palette(self.violin_palette_value)
        self.violin_palette_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.violin_palette_value.Bind(wx.EVT_COMBOBOX, self.on_update)

        violin_shade_color_label = wx.StaticText(self, -1, "Fill color:")
        self.violin_color_fill_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="violin.fill.color"
        )
        self.violin_color_fill_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        violin_shade_transparency_label = wx.StaticText(self, -1, "Fill transparency:")
        self.violin_fill_transparency_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_fill_under_transparency),
            min=0,
            max=1,
            initial=CONFIG.violin_fill_under_transparency,
            inc=0.25,
            size=(90, -1),
            name="violin.fill",
        )
        self.violin_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        violin_label_frequency_label = wx.StaticText(self, -1, "Label frequency:")
        self.violin_label_frequency_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.violin_labels_frequency),
            min=0,
            max=100,
            initial=CONFIG.violin_labels_frequency,
            inc=1,
            size=(45, -1),
            name="violin.label.reset",
        )
        self.violin_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.violin_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        violin_label_format_label = wx.StaticText(self, -1, "Label format:")
        self.violin_label_format_value = wx.Choice(
            self, -1, choices=CONFIG.violin_labels_format_choices, size=(-1, -1), name="violin.label.reset"
        )
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        plot_parameters_label = wx.StaticText(self, -1, "Plot parameters")
        set_item_font(plot_parameters_label)

        labels_parameters_label = wx.StaticText(self, -1, "Labels parameters")
        set_item_font(labels_parameters_label)

        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        # violin parameters
        n = 0
        grid.Add(plot_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_n_limit_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_n_limit_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_orientation_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_orientation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_spacing_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_spacing_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_min_percentage_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_min_percentage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_normalize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_normalize_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_smooth_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_smooth_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_smooth_sigma, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_smooth_sigma_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_line_style_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_line_same_as_fill_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.violin_color_line_btn, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(violin_color_scheme_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_colorScheme_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_colormap_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_palette, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_palette_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_shade_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_color_fill_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(violin_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_fill_transparency_value, (n, 1), flag=wx.EXPAND)
        # label parameters
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(labels_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_label_frequency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_label_frequency_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(violin_label_format_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.violin_label_format_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply violin parameters"""
        if self.import_evt:
            return
        CONFIG.violin_orientation = self.violin_orientation_value.GetStringSelection()
        CONFIG.violin_min_percentage = str2num(self.violin_min_percentage_value.GetValue())
        CONFIG.violin_spacing = str2num(self.violin_spacing_value.GetValue())
        CONFIG.violin_line_width = self.violin_line_width_value.GetValue()
        CONFIG.violin_line_style = self.violin_line_style_value.GetStringSelection()
        CONFIG.violin_color_scheme = self.violin_colorScheme_value.GetStringSelection()
        CONFIG.violin_palette = self.violin_palette_value.GetStringSelection()
        CONFIG.violin_colormap = self.violin_colormap_value.GetStringSelection()
        CONFIG.violin_normalize = self.violin_normalize_check.GetValue()
        CONFIG.violin_smooth = self.violin_smooth_value.GetValue()
        CONFIG.violin_smooth_sigma = self.violin_smooth_sigma_value.GetValue()
        CONFIG.violin_line_same_as_fill = self.violin_line_same_as_fill_check.GetValue()
        CONFIG.violin_fill_under_transparency = self.violin_fill_transparency_value.GetValue()
        CONFIG.violin_n_limit = self.violin_n_limit_value.GetValue()
        CONFIG.violin_labels_format = self.violin_label_format_value.GetStringSelection()
        CONFIG.violin_labels_frequency = int(self.violin_label_frequency_value.GetValue())

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update violin plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return

        if not source.startswith("violin."):
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

    def on_toggle_controls(self, evt):
        """Update violin controls"""
        CONFIG.violin_line_same_as_fill = self.violin_line_same_as_fill_check.GetValue()
        self.violin_color_line_btn.Enable(not CONFIG.violin_line_same_as_fill)

        CONFIG.violin_color_scheme = self.violin_colorScheme_value.GetStringSelection()
        self.violin_color_fill_btn.Enable(CONFIG.violin_color_scheme == "Same color")
        self.violin_colormap_value.Enable(CONFIG.violin_color_scheme == "Colormap")
        self.violin_palette_value.Enable(CONFIG.violin_color_scheme == "Color palette")

        CONFIG.violin_smooth = self.violin_smooth_value.GetValue()
        self.violin_smooth_sigma_value.Enable(CONFIG.violin_smooth)

        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "violin.line.color":
            CONFIG.violin_line_color = color_1
            self.violin_color_line_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "violin.fill.color":
            CONFIG.violin_fill_under_color = color_1
            self.violin_color_fill_btn.SetBackgroundColour(color_255)
            self.on_update(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.violin_n_limit_value.SetValue(CONFIG.violin_n_limit)
        self.violin_orientation_value.SetStringSelection(CONFIG.violin_orientation)
        self.violin_spacing_value.SetValue(CONFIG.violin_spacing)
        self.violin_min_percentage_value.SetValue(CONFIG.violin_min_percentage)
        self.violin_normalize_check.SetValue(CONFIG.violin_normalize)
        self.violin_smooth_value.SetValue(CONFIG.violin_smooth)
        self.violin_smooth_sigma_value.SetValue(CONFIG.violin_smooth_sigma)
        self.violin_line_width_value.SetValue(CONFIG.violin_line_width)
        self.violin_line_style_value.SetStringSelection(CONFIG.violin_line_style)
        self.violin_line_same_as_fill_check.SetValue(CONFIG.violin_line_same_as_fill)
        self.violin_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.violin_line_color))
        self.violin_colorScheme_value.SetStringSelection(CONFIG.violin_color_scheme)
        self.violin_colormap_value.SetStringSelection(CONFIG.violin_colormap)
        self.violin_palette_value.SetStringSelection(CONFIG.violin_palette)
        self.violin_color_fill_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.violin_fill_under_color))
        self.violin_fill_transparency_value.SetValue(CONFIG.violin_fill_under_transparency)
        self.violin_label_frequency_value.SetValue(CONFIG.violin_labels_frequency)
        self.violin_label_format_value.SetStringSelection(CONFIG.waterfall_labels_format)
        self.import_evt = False
