"""Extra configuration options of the UniDec panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.styles import Validator
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.visuals.utilities import on_change_color_palette
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelCustomiseUniDecVisuals(PanelSettingsBase):
    """Dialog window to customise UniDec visualisations"""

    mw_show_markers_check, mw_marker_size_value, contour_levels_value = None, None, None
    isolated_ms_marker_size_value, bar_width_value, bar_alpha_value = None, None, None
    bar_color_edge_check, bar_line_width_value, bar_marker_size_value = None, None, None
    color_scheme_value, colormap_value, color_palette_value = None, None, None
    unidec_labels_optimise_position_check, unidec_max_shown_lines_value, speedy_check = None, None, None
    unidec_maxIters_value, unidec_view_value, bar_edge_color_btn = None, None, None
    fit_line_color_btn, unidec_settings_value, heatmap_colormap = None, None, None

    def __init__(self, parent, view=None):
        PanelSettingsBase.__init__(self, parent, view)
        self.parent = parent
        self._view_register = dict()

    def setup(self):
        """Setup mixins"""
        self._config_mixin_setup()

    def on_close(self, evt, force: bool = False):
        """Close window"""
        self._config_mixin_teardown()
        super(PanelCustomiseUniDecVisuals, self).on_close(evt, force)

    def make_panel(self):
        """Make panel"""
        unidec_settings_label = wx.StaticText(self, -1, "Settings position:")
        self.unidec_settings_value = wx.Choice(self, -1, choices=CONFIG.unidec_settings_view_choices, size=(-1, -1))
        self.unidec_settings_value.SetStringSelection(CONFIG.unidec_settings_view)
        self.unidec_settings_value.Bind(wx.EVT_CHOICE, self.on_view_notification)

        unidec_view_label = wx.StaticText(self, -1, "Panel view:")
        self.unidec_view_value = wx.Choice(self, -1, choices=CONFIG.unidec_panel_view_choices, size=(-1, -1))
        self.unidec_view_value.SetStringSelection(CONFIG.unidec_panel_view)
        self.unidec_view_value.Bind(wx.EVT_CHOICE, self.on_view_notification)

        unidec_max_iters_label = wx.StaticText(self, wx.ID_ANY, "No. max iterations:")
        self.unidec_maxIters_value = wx.TextCtrl(self, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.unidec_maxIters_value.SetValue(str(CONFIG.unidec_panel_max_iterations))
        self.unidec_maxIters_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_max_shown_label = wx.StaticText(self, wx.ID_ANY, "No. max shown lines:")
        self.unidec_max_shown_lines_value = wx.TextCtrl(self, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.unidec_max_shown_lines_value.SetValue(str(CONFIG.unidec_panel_plot_individual_line_max_shown))
        self.unidec_max_shown_lines_value.Bind(wx.EVT_TEXT, self.on_apply)

        remove_label_overlap_label = wx.StaticText(self, wx.ID_ANY, "Optimise labels:")
        self.unidec_labels_optimise_position_check = make_checkbox(self, "")
        self.unidec_labels_optimise_position_check.SetValue(CONFIG.unidec_panel_plot_optimize_label_position)
        self.unidec_labels_optimise_position_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.unidec_labels_optimise_position_check, "Optimize label positions to avoid overlap.")

        # Color
        color_scheme_label = wx.StaticText(self, -1, "Color scheme:")
        self.color_scheme_value = wx.Choice(
            self, -1, choices=["Color palette", "Colormap"], size=(-1, -1), name="unidec.color_scheme"
        )
        self.color_scheme_value.SetStringSelection(CONFIG.unidec_panel_plot_color_scheme)
        self.color_scheme_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.color_scheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        cmap_list = CONFIG.colormap_choices[:]
        cmap_list.remove("jet")
        colormap_label = wx.StaticText(self, -1, "Colormap:")
        self.colormap_value = wx.Choice(self, -1, choices=cmap_list, size=(-1, -1), name="unidec.color_scheme")
        self.colormap_value.SetStringSelection(CONFIG.unidec_panel_plot_colormap)
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)

        palette_label = wx.StaticText(self, -1, "Color palette:")
        self.color_palette_value = BitmapComboBox(
            self, -1, choices=[], size=(160, -1), style=wx.CB_READONLY, name="unidec.color_scheme"
        )
        self._set_color_palette(self.color_palette_value)
        self.color_palette_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.color_palette_value.SetStringSelection(CONFIG.unidec_panel_plot_palette)

        # MS and MS Fit
        fit_line_color_label = wx.StaticText(self, -1, "Line color:")
        self.fit_line_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="unidec.fit.line"
        )
        self.fit_line_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.unidec_panel_plot_fit_line_color))
        self.fit_line_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # Zero-charge MS
        mw_show_markers = wx.StaticText(self, -1, "Show markers:")
        self.mw_show_markers_check = make_checkbox(self, "", name="unidec.mw.scatter")
        self.mw_show_markers_check.SetValue(CONFIG.unidec_panel_plot_mw_markers_show)
        self.mw_show_markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.mw_show_markers_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        mw_marker_size_label = wx.StaticText(self, -1, "Marker size:")
        self.mw_marker_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_mw_markers_size),
            min=1,
            max=100,
            initial=1,
            inc=5,
            size=(90, -1),
            name="unidec.mw.scatter",
        )
        self.mw_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.mw_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        # m/z vs charge
        speedy_label = wx.StaticText(self, wx.ID_ANY, "Quick plot:")
        self.speedy_check = make_checkbox(self, "", name="unidec.heatmap.data")
        self.speedy_check.SetValue(CONFIG.unidec_panel_plot_speed_heatmap)
        self.speedy_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.speedy_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        contour_levels_label = wx.StaticText(self, -1, "Contour levels:")
        self.contour_levels_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_contour_levels),
            min=25,
            max=200,
            initial=25,
            inc=25,
            size=(90, -1),
            name="unidec.heatmap.contour",
        )
        self.contour_levels_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.contour_levels_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        heatmap_colormap = wx.StaticText(self, -1, "Colormap:")
        self.heatmap_colormap = wx.Choice(
            self, -1, choices=CONFIG.colormap_choices, size=(-1, -1), name="unidec.heatmap.heatmap"
        )
        self.heatmap_colormap.SetStringSelection(CONFIG.unidec_panel_plot_colormap)
        self.heatmap_colormap.Bind(wx.EVT_CHOICE, self.on_apply)
        self.heatmap_colormap.Bind(wx.EVT_CHOICE, self.on_update_style)

        # MS with isolated species
        isolated_ms_marker_size_label = wx.StaticText(self, -1, "Marker size:")
        self.isolated_ms_marker_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_individual_markers_size),
            min=1,
            max=100,
            initial=1,
            inc=5,
            size=(90, -1),
            name="unidec.individual.scatter",
        )
        self.isolated_ms_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.isolated_ms_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        # Barchart
        bar_marker_size_label = wx.StaticText(self, -1, "Marker size:")
        self.bar_marker_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_bar_markers_size),
            min=1,
            max=100,
            initial=1,
            inc=5,
            size=(90, -1),
            name="unidec.barchart.scatter",
        )
        self.bar_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bar_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        bar_width_label = wx.StaticText(self, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_bar_width),
            min=0.01,
            max=10,
            inc=0.1,
            initial=CONFIG.unidec_panel_plot_bar_width,
            size=(90, -1),
            name="unidec.barchart.bar",
        )
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        bar_alpha_label = wx.StaticText(self, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_bar_fill_alpha),
            min=0,
            max=1,
            initial=CONFIG.unidec_panel_plot_bar_fill_alpha,
            inc=0.25,
            size=(90, -1),
            name="unidec.barchart.bar",
        )
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        bar_line_width_label = wx.StaticText(self, -1, "Edge line width:")
        self.bar_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.unidec_panel_plot_bar_line_width),
            min=0,
            max=5,
            initial=CONFIG.unidec_panel_plot_bar_line_width,
            inc=1,
            size=(90, -1),
            name="unidec.barchart.bar",
        )
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        bar_edge_color_label = wx.StaticText(self, -1, "Edge color:")
        self.bar_edge_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="unidec.barchart.bar"
        )
        self.bar_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.unidec_panel_plot_bar_line_color))
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        bar_color_edge_check_label = wx.StaticText(self, -1, "Same as fill:")
        self.bar_color_edge_check = make_checkbox(self, "", name="unidec.barchart.bar")
        self.bar_color_edge_check.SetValue(CONFIG.unidec_panel_plot_bar_line_same_as_fill)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        # general
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(set_item_font(wx.StaticText(self, -1, "General")), (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(unidec_settings_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_settings_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(unidec_view_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_view_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(unidec_max_iters_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_maxIters_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(unidec_max_shown_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_max_shown_lines_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(remove_label_overlap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_labels_optimise_position_check, (y, 1), flag=wx.EXPAND)
        # color scheme
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(set_item_font(wx.StaticText(self, -1, "Color scheme")), (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(color_scheme_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_scheme_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(colormap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(palette_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_palette_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(set_item_font(wx.StaticText(self, -1, "MS and Fit")), (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(fit_line_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_line_color_btn, (y, 1), flag=wx.EXPAND)
        # zero charge
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            set_item_font(wx.StaticText(self, -1, "Zero-charge MS")), (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER
        )
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(mw_show_markers, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_show_markers_check, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(mw_marker_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_marker_size_value, (y, 1), flag=wx.EXPAND)
        # mw
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            set_item_font(wx.StaticText(self, -1, "m/z vs charge | MW vs charge")),
            (y, 0),
            wx.GBSpan(1, 2),
            flag=wx.ALIGN_CENTER,
        )
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(speedy_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.speedy_check, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(contour_levels_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.contour_levels_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(heatmap_colormap, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_colormap, (y, 1), flag=wx.EXPAND)
        # isolated
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            set_item_font(wx.StaticText(self, -1, "MS with isolated species")),
            (y, 0),
            wx.GBSpan(1, 2),
            flag=wx.ALIGN_CENTER,
        )
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(isolated_ms_marker_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.isolated_ms_marker_size_value, (y, 1), flag=wx.EXPAND)
        # bar chart
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(
            set_item_font(wx.StaticText(self, -1, "Peak intensities (barchart)")),
            (y, 0),
            wx.GBSpan(1, 2),
            flag=wx.ALIGN_CENTER,
        )
        y += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(bar_marker_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_marker_size_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(bar_width_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_width_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(bar_alpha_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_alpha_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(bar_line_width_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_line_width_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(bar_edge_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_edge_color_btn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(bar_color_edge_check_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bar_color_edge_check, (y, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        return self

    def on_change_color_palette(self, evt):
        """Update color palette"""
        if self.import_evt:
            return

        CONFIG.current_palette = self.plot_palette_value.GetStringSelection()
        on_change_color_palette()
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Change color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        if source == "unidec.barchart.bar":
            CONFIG.unidec_panel_plot_bar_line_color = color_1
            self.bar_edge_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)
        elif source == "unidec.fit.line":
            CONFIG.unidec_panel_plot_fit_line_color = color_1
            self.fit_line_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)

    def register_view(self, starts_with: str, view):
        """Register view with name so it can be matched with the name of the event"""
        if starts_with not in self._view_register:
            self._view_register[starts_with] = []
        self._view_register[starts_with].append(view)

    def on_update_style(self, evt):
        """Update 1d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("unidec"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source.split("unidec.")[-1]

        for key, views in self._view_register.items():
            if name.startswith(key):
                for view in views:
                    try:
                        view.update_style(name)
                    except (AttributeError, KeyError):
                        LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_apply(self, evt):
        """Update configuration"""
        CONFIG.unidec_panel_plot_mw_markers_show = self.mw_show_markers_check.GetValue()
        CONFIG.unidec_panel_plot_mw_markers_size = self.mw_marker_size_value.GetValue()
        CONFIG.unidec_panel_plot_contour_levels = int(self.contour_levels_value.GetValue())
        CONFIG.unidec_panel_plot_individual_markers_size = self.isolated_ms_marker_size_value.GetValue()
        CONFIG.unidec_panel_plot_bar_width = self.bar_width_value.GetValue()
        CONFIG.unidec_panel_plot_bar_fill_alpha = self.bar_alpha_value.GetValue()
        CONFIG.unidec_panel_plot_bar_line_same_as_fill = self.bar_color_edge_check.GetValue()
        CONFIG.unidec_panel_plot_bar_line_width = self.bar_line_width_value.GetValue()
        CONFIG.unidec_panel_plot_bar_markers_size = self.bar_marker_size_value.GetValue()
        CONFIG.unidec_panel_plot_color_scheme = self.color_scheme_value.GetStringSelection()
        CONFIG.unidec_panel_plot_colormap = self.colormap_value.GetStringSelection()
        CONFIG.unidec_panel_plot_heatmap_colormap = self.heatmap_colormap.GetStringSelection()
        CONFIG.unidec_panel_plot_palette = self.color_palette_value.GetStringSelection()
        CONFIG.unidec_panel_plot_optimize_label_position = self.unidec_labels_optimise_position_check.GetValue()
        CONFIG.unidec_panel_plot_speed_heatmap = self.speedy_check.GetValue()
        CONFIG.unidec_panel_plot_individual_line_max_shown = str2int(self.unidec_max_shown_lines_value.GetValue())
        CONFIG.unidec_panel_max_iterations = str2int(self.unidec_maxIters_value.GetValue())
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.mw_show_markers_check.SetValue(CONFIG.unidec_panel_plot_mw_markers_show)
        self.mw_marker_size_value.SetValue(CONFIG.unidec_panel_plot_mw_markers_size)
        self.contour_levels_value.SetValue(CONFIG.unidec_panel_plot_contour_levels)
        self.isolated_ms_marker_size_value.SetValue(CONFIG.unidec_panel_plot_individual_markers_size)
        self.bar_width_value.SetValue(CONFIG.unidec_panel_plot_bar_width)
        self.bar_color_edge_check.SetValue(CONFIG.unidec_panel_plot_bar_line_same_as_fill)
        self.bar_line_width_value.SetValue(CONFIG.unidec_panel_plot_bar_line_width)
        self.bar_marker_size_value.SetValue(CONFIG.unidec_panel_plot_bar_markers_size)
        self.unidec_labels_optimise_position_check.SetValue(CONFIG.unidec_panel_plot_optimize_label_position)
        self.speedy_check.SetValue(CONFIG.unidec_panel_plot_speed_heatmap)
        self.unidec_max_shown_lines_value.SetValue(str(CONFIG.unidec_panel_plot_individual_line_max_shown))
        self.unidec_maxIters_value.SetValue(str(CONFIG.unidec_panel_max_iterations))
        self.color_scheme_value.SetStringSelection(CONFIG.unidec_panel_plot_color_scheme)
        self.colormap_value.SetStringSelection(CONFIG.unidec_panel_plot_colormap)
        self.color_palette_value.SetStringSelection(CONFIG.unidec_panel_plot_palette)
        self.import_evt = False

    def on_toggle_controls(self, evt):
        """Toggle controls"""
        CONFIG.unidec_panel_plot_color_scheme = self.color_scheme_value.GetStringSelection()
        if CONFIG.unidec_panel_plot_color_scheme == "Colormap":
            self.colormap_value.Enable()
            self.color_palette_value.Disable()
        else:
            self.colormap_value.Disable()
            self.color_palette_value.Enable()
        self._parse_evt(evt)

    def on_view_notification(self, _evt):
        """Show notification to the user"""
        CONFIG.unidec_panel_view = self.unidec_view_value.GetStringSelection()
        CONFIG.unidec_settings_view = self.unidec_settings_value.GetStringSelection()

        DialogBox(
            title="Warning",
            msg="This will not take effect until the UniDec processing panel is restarted",
            kind="Warning",
        )


def _main():
    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelCustomiseUniDecVisuals(self)

    app = wx.App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
