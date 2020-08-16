"""Extra configuration options of the UniDec panel"""
# Third-party imports
import wx
from wx.adv import BitmapComboBox

# Local imports
from origami.styles import Dialog
from origami.styles import Validator
from origami.utils.color import convert_rgb_1_to_255
from origami.icons.assets import Colormaps
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.gui_elements.mixins import ColorGetterMixin
from origami.gui_elements.mixins import ColorPaletteMixin
from origami.gui_elements.mixins import ConfigUpdateMixin
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.misc_dialogs import DialogBox


class DialogCustomiseUniDecVisuals(Dialog, ConfigUpdateMixin, ColorGetterMixin, ColorPaletteMixin):
    """Dialog window to customise UniDec visualisations"""

    mw_show_markers_check, mw_marker_size_value, contour_levels_value = None, None, None
    isolated_ms_marker_size_value, bar_width_value, bar_alpha_value = None, None, None
    bar_color_edge_check, bar_line_width_value, bar_marker_size_value = None, None, None
    color_scheme_value, colormap_value, color_palette_value = None, None, None
    unidec_labels_optimise_position_check, unidec_max_shown_lines_value, speedy_check = None, None, None
    unidec_maxIters_value, unidec_view_value, bar_edge_color_btn = None, None, None
    fit_line_color_btn, unidec_settings_value = None, None

    def __init__(self, parent):
        Dialog.__init__(self, parent, title="UniDec parameters...")

        self.parent = parent
        self._colormaps = Colormaps()

        self.make_gui()
        self.on_toggle_controls(None)
        self.Layout()
        self.CenterOnParent()
        self.SetFocus()

    def setup(self):
        """Setup mixins"""
        self._config_mixin_setup()

    def on_close(self, evt, force: bool = False):
        """Close window"""
        self._config_mixin_teardown()
        super(DialogCustomiseUniDecVisuals, self).on_close(evt, force)

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        general_parameters_label = wx.StaticText(panel, -1, "General")
        set_item_font(general_parameters_label)

        unidec_settings_label = wx.StaticText(panel, -1, "Settings position:")
        self.unidec_settings_value = wx.Choice(
            panel, -1, choices=CONFIG.unidec_plot_settings_view_choices, size=(-1, -1)
        )
        self.unidec_settings_value.SetStringSelection(CONFIG.unidec_plot_settings_view)
        self.unidec_settings_value.Bind(wx.EVT_CHOICE, self.on_view_notification)

        unidec_view_label = wx.StaticText(panel, -1, "Panel view:")
        self.unidec_view_value = wx.Choice(panel, -1, choices=CONFIG.unidec_plot_panel_view_choices, size=(-1, -1))
        self.unidec_view_value.SetStringSelection(CONFIG.unidec_plot_panel_view)
        self.unidec_view_value.Bind(wx.EVT_CHOICE, self.on_view_notification)

        unidec_max_iters_label = wx.StaticText(panel, wx.ID_ANY, "No. max iterations:")
        self.unidec_maxIters_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.unidec_maxIters_value.SetValue(str(CONFIG.unidec_panel_max_iterations))
        self.unidec_maxIters_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_max_shown_label = wx.StaticText(panel, wx.ID_ANY, "No. max shown lines:")
        self.unidec_max_shown_lines_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.unidec_max_shown_lines_value.SetValue(str(CONFIG.unidec_panel_plot_line_max_shown))
        self.unidec_max_shown_lines_value.Bind(wx.EVT_TEXT, self.on_apply)

        remove_label_overlap_label = wx.StaticText(panel, wx.ID_ANY, "Optimise label position:")
        self.unidec_labels_optimise_position_check = make_checkbox(panel, "")
        self.unidec_labels_optimise_position_check.SetValue(CONFIG.unidec_panel_plot_optimize_label_position)
        self.unidec_labels_optimise_position_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # MS and MS Fit
        ms_fit_parameters_label = wx.StaticText(panel, -1, "MS and Fit")
        set_item_font(ms_fit_parameters_label)

        fit_line_color_label = wx.StaticText(panel, -1, "Line color:")
        self.fit_line_color_btn = wx.Button(
            panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="unidec.fit"
        )
        self.fit_line_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.unidec_plot_fit_lineColor))
        self.fit_line_color_btn.Bind(wx.EVT_BUTTON, self.on_change_color)

        # m/z vs charge
        contour_parameters_label = wx.StaticText(panel, -1, "m/z vs charge | MW vs charge")
        set_item_font(contour_parameters_label)

        speedy_label = wx.StaticText(panel, wx.ID_ANY, "Quick plot:")
        self.speedy_check = make_checkbox(panel, "")
        self.speedy_check.SetValue(CONFIG.unidec_panel_plot_speed_heatmap)
        self.speedy_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        contour_levels_label = wx.StaticText(panel, -1, "Contour levels:")
        self.contour_levels_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.unidec_plot_contour_levels), min=25, max=200, initial=25, inc=25, size=(90, -1)
        )
        self.contour_levels_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # Zero-charge MS
        zero_charge_parameters_label = wx.StaticText(panel, -1, "Zero-charge MS")
        set_item_font(zero_charge_parameters_label)

        mw_show_markers = wx.StaticText(panel, -1, "Show markers:")
        self.mw_show_markers_check = make_checkbox(panel, "")
        self.mw_show_markers_check.SetValue(CONFIG.unidec_plot_MW_showMarkers)
        self.mw_show_markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        mw_marker_size_label = wx.StaticText(panel, -1, "Marker size:")
        self.mw_marker_size_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.unidec_plot_MW_markerSize), min=1, max=100, initial=1, inc=5, size=(90, -1)
        )
        self.mw_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        #         # Zero-charge MS
        #         MW_staticBox = make_staticbox(panel, "Zero-charge Mass Spectrum", size=(-1, -1), color=wx.BLACK)
        #         MW_staticBox.SetSize((-1,-1))
        #         MW_box_sizer = wx.StaticBoxSizer(MW_staticBox, wx.HORIZONTAL)
        #
        #         MW_show_markers = wx.StaticText(panel, -1, "Show markers:")
        #         self.MW_show_markers_check = make_checkbox(panel, u"")
        #         self.MW_show_markers_check.SetValue(CONFIG.unidec_plot_MW_showMarkers)
        #         self.MW_show_markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        #
        #         MW_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        #         self.MW_markerSize_value = wx.SpinCtrlDouble(panel, -1,
        #                                                value=str(CONFIG.unidec_plot_MW_markerSize),
        #                                                min=1, max=100, initial=1, inc=5,
        #                                                size=(90, -1))
        #         self.MW_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        #
        #         grid = wx.GridBagSizer(2, 2)
        #         y = 0
        #         grid.Add(MW_show_markers, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        #         grid.Add(self.MW_show_markers_check, (y,1), flag=wx.EXPAND)
        #         y += 1
        #         grid.Add(MW_markerSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        #         grid.Add(self.MW_markerSize_value, (y,1), flag=wx.EXPAND)
        #         MW_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        # MS with isolated species
        isolated_parameters_label = wx.StaticText(panel, -1, "MS with isolated species")
        set_item_font(isolated_parameters_label)

        isolated_ms_marker_size_label = wx.StaticText(panel, -1, "Marker size:")
        self.isolated_ms_marker_size_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_plot_isolatedMS_markerSize),
            min=1,
            max=100,
            initial=1,
            inc=5,
            size=(90, -1),
        )
        self.isolated_ms_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # Barchart
        barchart_parameters_label = wx.StaticText(panel, -1, "Peak intensities (barchart)")
        set_item_font(barchart_parameters_label)

        bar_marker_size_label = wx.StaticText(panel, -1, "Marker size:")
        self.bar_marker_size_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.unidec_plot_bar_markerSize), min=1, max=100, initial=1, inc=5, size=(90, -1)
        )
        self.bar_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_width_label = wx.StaticText(panel, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_plot_bar_width),
            min=0.01,
            max=10,
            inc=0.1,
            initial=CONFIG.unidec_plot_bar_width,
            size=(90, -1),
        )
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_alpha_label = wx.StaticText(panel, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_plot_bar_alpha),
            min=0,
            max=1,
            initial=CONFIG.unidec_plot_bar_alpha,
            inc=0.25,
            size=(90, -1),
        )
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_line_width_label = wx.StaticText(panel, -1, "Edge line width:")
        self.bar_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_plot_bar_lineWidth),
            min=0,
            max=5,
            initial=CONFIG.unidec_plot_bar_lineWidth,
            inc=1,
            size=(90, -1),
        )
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bar_edge_color_label = wx.StaticText(panel, -1, "Edge color:")
        self.bar_edge_color_btn = wx.Button(
            panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="unidec.bar"
        )
        self.bar_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.unidec_plot_bar_edge_color))
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_change_color)

        bar_color_edge_check_label = wx.StaticText(panel, -1, "Same as fill:")
        self.bar_color_edge_check = make_checkbox(panel, "")
        self.bar_color_edge_check.SetValue(CONFIG.unidec_plot_bar_sameAsFill)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # Color
        color_parameters_label = wx.StaticText(panel, -1, "Color scheme")
        set_item_font(color_parameters_label)

        color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.color_scheme_value = wx.Choice(
            panel, -1, choices=["Color palette", "Colormap"], size=(-1, -1), name="color"
        )
        self.color_scheme_value.SetStringSelection(CONFIG.unidec_plot_color_scheme)
        self.color_scheme_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.color_scheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        cmap_list = CONFIG.colormap_choices[:]
        cmap_list.remove("jet")
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.colormap_value = wx.Choice(panel, -1, choices=cmap_list, size=(-1, -1), name="color")
        self.colormap_value.SetStringSelection(CONFIG.unidec_plot_colormap)
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)

        palette_label = wx.StaticText(panel, -1, "Color palette:")
        self.color_palette_value = BitmapComboBox(panel, -1, choices=[], size=(160, -1), style=wx.CB_READONLY)
        self._set_color_palette(self.color_palette_value)
        self.color_palette_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.color_palette_value.SetStringSelection(CONFIG.unidec_plot_palette)

        # general
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(general_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
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
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(ms_fit_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(fit_line_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_line_color_btn, (y, 1), flag=wx.EXPAND)
        # mw
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(contour_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(speedy_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.speedy_check, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(contour_levels_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.contour_levels_value, (y, 1), flag=wx.EXPAND)
        y += 1
        # zero charge
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(zero_charge_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(mw_show_markers, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_show_markers_check, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(mw_marker_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_marker_size_value, (y, 1), flag=wx.EXPAND)
        # isolated
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(isolated_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(isolated_ms_marker_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.isolated_ms_marker_size_value, (y, 1), flag=wx.EXPAND)
        # bar chart
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(barchart_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
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
        # color scheme
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(color_parameters_label, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(color_scheme_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_scheme_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(colormap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(palette_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_palette_value, (y, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_change_color_palette(self, evt):
        """Change color palette"""

    def on_change_color(self, evt):
        """Change color"""
        source = evt.GetEventObject().GetName()

        color_255, color_1, _ = self.on_get_color(None)
        if color_1 is None:
            return None

        if source == "unidec.bar":
            CONFIG.unidec_plot_bar_edge_color = color_1
            self.bar_edge_color_btn.SetBackgroundColour(color_255)
        elif source == "unidec.fit":
            CONFIG.unidec_plot_fit_lineColor = color_1
            self.fit_line_color_btn.SetBackgroundColour(color_255)

    def on_apply(self, evt):
        """Update configuration"""

        CONFIG.unidec_plot_MW_showMarkers = self.mw_show_markers_check.GetValue()
        CONFIG.unidec_plot_MW_markerSize = self.mw_marker_size_value.GetValue()
        CONFIG.unidec_plot_contour_levels = int(self.contour_levels_value.GetValue())
        CONFIG.unidec_plot_isolatedMS_markerSize = self.isolated_ms_marker_size_value.GetValue()
        CONFIG.unidec_plot_bar_width = self.bar_width_value.GetValue()
        CONFIG.unidec_plot_bar_alpha = self.bar_alpha_value.GetValue()
        CONFIG.unidec_plot_bar_sameAsFill = self.bar_color_edge_check.GetValue()
        CONFIG.unidec_plot_bar_lineWidth = self.bar_line_width_value.GetValue()
        CONFIG.unidec_plot_bar_markerSize = self.bar_marker_size_value.GetValue()
        CONFIG.unidec_plot_color_scheme = self.color_scheme_value.GetStringSelection()
        CONFIG.unidec_plot_colormap = self.colormap_value.GetStringSelection()
        CONFIG.unidec_plot_palette = self.color_palette_value.GetStringSelection()

        CONFIG.unidec_panel_plot_optimize_label_position = self.unidec_labels_optimise_position_check.GetValue()
        CONFIG.unidec_panel_plot_speed_heatmap = self.speedy_check.GetValue()
        CONFIG.unidec_panel_plot_line_max_shown = str2int(self.unidec_max_shown_lines_value.GetValue())
        CONFIG.unidec_panel_max_iterations = str2int(self.unidec_maxIters_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_view_notification(self, _evt):
        """Show notification to the user"""
        CONFIG.unidec_plot_panel_view = self.unidec_view_value.GetStringSelection()
        CONFIG.unidec_plot_settings_view = self.unidec_settings_value.GetStringSelection()

        DialogBox(
            title="Warning",
            msg="This will not take effect until the UniDec processing panel is restarted",
            kind="Warning",
        )

    def on_toggle_controls(self, evt):
        """Toggle controls"""
        CONFIG.unidec_plot_color_scheme = self.color_scheme_value.GetStringSelection()
        if CONFIG.unidec_plot_color_scheme == "Colormap":
            self.colormap_value.Enable()
            self.color_palette_value.Disable()
        else:
            self.colormap_value.Disable()
            self.color_palette_value.Enable()

        if evt is not None:
            evt.Skip()


def _main():
    app = wx.App()
    ex = DialogCustomiseUniDecVisuals(None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
