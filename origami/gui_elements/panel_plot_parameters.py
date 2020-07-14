"""Plot parameters"""
# Standard library imports
import time
import logging

# Third-party imports
import wx.lib.scrolledpanel
from wx.adv import BitmapComboBox

# Local imports
from origami.ids import ID_extraSettings_logging
from origami.ids import ID_extraSettings_boxColor
from origami.ids import ID_extraSettings_lineColor_1D
from origami.ids import ID_extraSettings_bar_edgeColor
from origami.ids import ID_extraSettings_verticalColor
from origami.ids import ID_extraSettings_lineColor_rmsd
from origami.ids import ID_extraSettings_markerColor_1D
from origami.ids import ID_extraSettings_horizontalColor
from origami.ids import ID_extraSettings_labelColor_rmsd
from origami.ids import ID_extraSettings_autoSaveSettings
from origami.ids import ID_extraSettings_lineColour_violin
from origami.ids import ID_extraSettings_edgeMarkerColor_1D
from origami.ids import ID_extraSettings_shadeColour_violin
from origami.ids import ID_extraSettings_shadeUnderColor_1D
from origami.ids import ID_extraSettings_underlineColor_rmsd
from origami.ids import ID_extraSettings_lineColour_waterfall
from origami.ids import ID_extraSettings_shadeColour_waterfall
from origami.styles import MiniFrame
from origami.styles import set_tooltip
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.styles import make_toggle_btn
from origami.utils.color import convert_rgb_1_to_255
from origami.icons.assets import Colormaps
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.dialog_color_picker import DialogColorPicker

logger = logging.getLogger(__name__)

PANEL_SPACE_MAIN = 2
CTRL_SIZE = 60
ALIGN_CV_R = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT


class PanelVisualisationSettingsEditor(MiniFrame):
    """Extra settings panel."""

    # ui elements
    main_book = None
    plot_tick_fontsize_value, plot_tick_font_weight_check, plot_label_fontsize_value = None, None, None
    plot_label_font_weight_check, plot_title_fontsize_value, plot1d_title_font_weight_check = None, None, None
    plot_annotation_fontsize_value, plot_annotation_font_weight_check, plot_axis_on_off_check = None, None, None
    plot_left_spines_check, plot_right_spines_check, plot_top_spines_check = None, None, None
    plot_bottom_spines_check, plot_left_ticks_check, plot_right_ticks_check = None, None, None
    plot_top_ticks_check, plot_bottom_ticks_check, plot_left_tick_labels_check = None, None, None
    plot_right_tick_labels_check, plot_top_tick_labels_check, plot_bottom_tick_labels_check = None, None, None
    plot_padding_value, plot_frame_width_value, plot_palette_value, plot_style_value = None, None, None, None
    colorbar_tgl, colorbar_position_value, colorbar_width_value = None, None, None
    colorbar_pad_value, colorbar_fontsize_value, colorbar_label_format = None, None, None
    colorbar_outline_width_value, colorbar_label_color_btn, colorbar_outline_color_btn = None, None, None
    legend_toggle, legend_position_value, legend_columns_value = None, None, None
    legend_fontsize_value, legend_frame_check, legend_alpha_value = None, None, None
    legend_marker_size_value, legend_n_markers_value, legend_marker_before_check = None, None, None
    legend_fancybox_check, legend_patch_alpha_value, violin_label_format_value = None, None, None
    violin_orientation_value, violin_min_percentage_value, violin_spacing_value = None, None, None
    violin_line_width_value, violin_line_style_value, violin_colorScheme_value = None, None, None
    violin_color_scheme_msg, violin_colormap_value, violin_normalize_check = None, None, None
    violin_line_same_as_fill_check, violin_fill_transparency_value, violin_n_limit_value = None, None, None
    violin_color_line_btn, violin_color_fill_btn, waterfall_color_line_btn = None, None, None
    waterfall_color_fill_btn, waterfall_label_y_offset_value = None, None
    violin_label_frequency_value, waterfall_offset_value, waterfall_label_format_value = None, None, None
    waterfall_fill_n_limit_value, waterfall_fill_transparency_value, waterfall_fill_under_check = None, None, None
    waterfall_label_font_weight_check, waterfall_label_font_size_value = None, None
    waterfall_increment_value, waterfall_line_width_value, waterfall_line_style_value = None, None, None
    waterfall_reverse_check, waterfall_colorScheme_value, waterfall_colorScheme_msg = None, None, None
    waterfall_label_x_offset_value, waterfall_label_frequency_value, waterfall_showLabels_check = None, None, None
    waterfall_line_sameAsShade_check, waterfall_normalize_check, waterfall_colormap_value = None, None, None
    general_left_value, general_bottom_value, general_width_value = None, None, None
    general_height_value, general_width_inch_value, general_height_inch_value = None, None, None
    general_plot_name_value, zoom_extract_crossover_1d_value, zoom_extract_crossover_2d_value = None, None, None
    zoom_zoom_vertical_color_btn, zoom_zoom_horizontal_color_btn, zoom_zoom_box_color_btn = None, None, None
    zoom_sensitivity_value, general_log_to_file_check, general_auto_save_check = None, None, None
    rmsd_position_value, rmsd_fontsize_value, rmsd_font_weight_check = None, None, None
    rmsd_x_rotation_value, rmsd_y_rotation_value, rmsd_line_style_value = None, None, None
    rmsd_line_hatch_value, rmsd_alpha_value, rmsd_vspace_value = None, None, None
    rmsd_add_labels_check, rmsd_matrix_color_fmt, rmsd_matrix_font_weight_check = None, None, None
    rmsd_matrix_fontsize, rmsd_matrix_font_color_btn, rmsd_x_position_value = None, None, None
    rmsd_y_position_value, rmsd_color_btn, rmsd_line_width_value = None, None, None
    rmsd_color_line_btn, rmsd_underline_color_btn = None, None
    plot2d_update_btn, plot2d_replot_btn, plot2d_colormap_value = None, None, None
    plot2d_override_colormap_check, plot2d_plot_type_value, plot2d_interpolation_value = None, None, None
    plot2d_normalization_value, plot2d_min_value, plot2d_mid_value = None, None, None
    plot2d_max_value, plot2d_normalization_gamma_value, plot3d_grids_check = None, None, None
    plot3d_plot_type_value, plot3d_shade_check, plot3d_ticks_check = None, None, None
    plot3d_spines_check, plot3d_labels_check, plot3d_update_btn = None, None, None
    plot3d_replot_btn, plot1d_update_btn, plot1d_replot_btn = None, None, None
    plot1d_line_width_value, plot1d_line_color_btn, plot1d_line_style_value = None, None, None
    plot1d_underline_check, plot1d_underline_alpha_value, plot1d_underline_color_btn = None, None, None
    plot1d_marker_shape_value, plot1d_marker_size_value, plot1d_alpha_value = None, None, None
    plot1d_marker_color_btn, plot1d_marker_edge_color_check, plot1d_marker_edge_color_btn = None, None, None
    bar_width_value, bar_alpha_value, bar_line_width_value = None, None, None
    bar_color_edge_check, bar_edge_color_btn = None, None

    def __init__(self, parent, presenter, window: str = None):
        MiniFrame.__init__(self, parent, title="Plot parameters")
        t_start = time.time()
        self.view = parent
        self.presenter = presenter
        self._colormaps = Colormaps()

        self.import_evt = True
        self.current_page = None
        self._switch = -1

        # make gui items
        self.make_gui()

        if window:
            self.on_set_page(window)

        # # fire-up some events
        # self.on_toggle_controls_1d(evt=None)
        # self.on_toggle_controls_2d(evt=None)
        self.on_toggle_controls_colorbar(evt=None)
        self.on_toggle_controls_legend(evt=None)
        # self.on_toggle_controls_waterfall(evt=None)
        # self.on_toggle_controls_violin(evt=None)
        # self.on_toggle_controls_rmsd(evt=None)
        # self.on_toggle_controls_zoom(evt=None)

        # self._recalculate_rmsd_position(evt=None)
        # self.on_update_plot_sizes(evt=None)
        # self.on_page_changed(evt=None)

        logger.info(f"Start-up took {report_time(t_start)}")

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.import_evt = False
        self.CenterOnParent()

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)
        elif key_code == 49:
            self.on_replot_1d(evt=None)
        elif key_code == 50:
            self.on_replot_2d(evt=None)
        elif key_code == 51:
            self.on_replot_3d(evt=None)

        if evt is not None:
            evt.Skip()

    def on_page_changed(self, _evt):
        """Change window"""
        t_start = time.time()
        self.current_page = self.main_book.GetPageText(self.main_book.GetSelection())

        # when the window is changed, the layout can be incorrect, hence we have to "reset it" on each occasion
        # basically a hack that kind of works...
        _size = self.GetSize()
        self._switch = 1 if self._switch == -1 else -1
        self.SetSize((_size[0] + self._switch, _size[1] + self._switch))
        self.SetSize(_size)
        self.SetMinSize(_size)

        self.SetFocus()
        logger.debug(f"Changed window to `{self.current_page}` in {report_time(t_start)}")

    def on_set_page(self, window: str):
        """Change page"""
        self.main_book.SetSelection(CONFIG.extraParamsWindow[window])
        self.on_page_changed(None)

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        CONFIG._windowSettings["Plot parameters"]["show"] = False  # noqa
        CONFIG.extraParamsWindow_on_off = False
        if hasattr(self.view, "window_mgr"):
            self.view.window_mgr.GetPane(self).Hide()  # noqa
            self.view.window_mgr.Update()  # noqa

    def make_gui(self):
        """Make UI"""
        # Setup notebook
        self.main_book = wx.Choicebook(self, wx.ID_ANY, style=wx.CHB_DEFAULT)

        # general
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_general(panel), "General", False)

        # plot 1D
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_1d(panel), "Plot 1D", False)

        # plot 2D
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_2d(panel), "Plot 2D", False)

        # plot 3D
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_3d(panel), "Plot 3D", False)

        # colorbar
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_colorbar(panel), "Colorbar", False)

        # legend
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_legend(panel), "Legend", False)

        # rmsd
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_rmsd(panel), "RMSD", False)

        # waterfall
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_waterfall(panel), "Waterfall", False)

        # violin
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_violin(panel), "Violin", False)

        # plot sizes
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_plot_sizes(panel), "Plot sizes", False)

        # plot sizes
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.main_book)
        panel.SetupScrolling()
        self.main_book.AddPage(self.make_panel_ui_behaviour(panel), "UI behaviour", False)

        # fit sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.main_book, 1, wx.EXPAND | wx.ALL, 2)
        self.main_book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_page_changed)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetMinSize((600, 400))
        self.Layout()
        self.SetFocus()
        self.Show(True)

    def make_panel_general(self, panel):
        """General settings"""
        plot_axis_on_off = wx.StaticText(panel, -1, "Show frame:")
        self.plot_axis_on_off_check = make_checkbox(panel, "", name="frame")
        self.plot_axis_on_off_check.SetValue(CONFIG.axisOnOff_1D)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_axis_on_off_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_general)

        plot_spines = wx.StaticText(panel, -1, "Line:")
        self.plot_left_spines_check = make_checkbox(panel, "Left", name="frame")
        self.plot_left_spines_check.SetValue(CONFIG.spines_left_1D)
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_left_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_spines_check = make_checkbox(panel, "Right", name="frame")
        self.plot_right_spines_check.SetValue(CONFIG.spines_right_1D)
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_right_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_spines_check = make_checkbox(panel, "Top", name="frame")
        self.plot_top_spines_check.SetValue(CONFIG.spines_top_1D)
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_top_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update_1d)

        self.plot_bottom_spines_check = make_checkbox(panel, "Bottom", name="frame")
        self.plot_bottom_spines_check.SetValue(CONFIG.spines_bottom_1D)
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_bottom_spines_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.plot_left_ticks_check = make_checkbox(panel, "Left", name="frame")
        self.plot_left_ticks_check.SetValue(CONFIG.ticks_left_1D)
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_left_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_ticks_check = make_checkbox(panel, "Right", name="frame")
        self.plot_right_ticks_check.SetValue(CONFIG.ticks_right_1D)
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_right_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_ticks_check = make_checkbox(panel, "Top", name="frame")
        self.plot_top_ticks_check.SetValue(CONFIG.ticks_top_1D)
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_top_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_ticks_check = make_checkbox(panel, "Bottom", name="frame")
        self.plot_bottom_ticks_check.SetValue(CONFIG.ticks_bottom_1D)
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_bottom_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_labels = wx.StaticText(panel, -1, "Tick labels:")
        self.plot_left_tick_labels_check = make_checkbox(panel, "Left", name="frame")
        self.plot_left_tick_labels_check.SetValue(CONFIG.tickLabels_left_1D)
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_left_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_right_tick_labels_check = make_checkbox(panel, "Right", name="frame")
        self.plot_right_tick_labels_check.SetValue(CONFIG.tickLabels_right_1D)
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_right_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_top_tick_labels_check = make_checkbox(panel, "Top", name="frame")
        self.plot_top_tick_labels_check.SetValue(CONFIG.tickLabels_top_1D)
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_top_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        self.plot_bottom_tick_labels_check = make_checkbox(panel, "Bottom", name="frame")
        self.plot_bottom_tick_labels_check.SetValue(CONFIG.tickLabels_bottom_1D)
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_bottom_tick_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_frame_width = wx.StaticText(panel, -1, "Frame width:")
        self.plot_frame_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.frameWidth_1D),
            min=0,
            max=10,
            initial=CONFIG.frameWidth_1D,
            inc=1,
            size=(90, -1),
            name="frame",
        )
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_frame_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_padding = wx.StaticText(panel, -1, "Label pad:")
        self.plot_padding_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.labelPad_1D),
            min=0,
            max=100,
            initial=CONFIG.labelPad_1D,
            inc=5,
            size=(90, -1),
            name="fonts",
        )
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot_title_fontsize = wx.StaticText(panel, -1, "Title font size:")
        self.plot_title_fontsize_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.titleFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.titleFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_title_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot1d_title_font_weight_check = make_checkbox(panel, "Bold", name="fonts")
        self.plot1d_title_font_weight_check.SetValue(CONFIG.titleFontWeight_1D)
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot1d_title_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_label_fontsize = wx.StaticText(panel, -1, "Label font size:")
        self.plot_label_fontsize_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.labelFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.labelFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_label_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_label_font_weight_check = make_checkbox(panel, "Bold", name="fonts")
        self.plot_label_font_weight_check.SetValue(CONFIG.labelFontWeight_1D)
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        plot_tick_fontsize = wx.StaticText(panel, -1, "Tick font size:")
        self.plot_tick_fontsize_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.tickFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.tickFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_tick_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_tick_font_weight_check = make_checkbox(panel, "Bold", name="fonts")
        self.plot_tick_font_weight_check.SetValue(CONFIG.tickFontWeight_1D)
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_tick_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)
        self.plot_tick_font_weight_check.Disable()

        plot_annotation_fontsize = wx.StaticText(panel, -1, "Annotation font size:")
        self.plot_annotation_fontsize_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.annotationFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.annotationFontSize_1D,
            inc=2,
            size=(90, -1),
            name="fonts",
        )
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.plot_annotation_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        self.plot_annotation_font_weight_check = make_checkbox(panel, "Bold", name="fonts")
        self.plot_annotation_font_weight_check.SetValue(CONFIG.annotationFontWeight_1D)
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.plot_annotation_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update)

        style_label = wx.StaticText(panel, -1, "Style:")
        self.plot_style_value = wx.Choice(panel, -1, choices=CONFIG.styles, size=(-1, -1))
        self.plot_style_value.SetStringSelection(CONFIG.currentStyle)
        self.plot_style_value.Bind(wx.EVT_CHOICE, self.on_change_plot_style)

        plot_palette = wx.StaticText(panel, -1, "Color palette:")
        self.plot_palette_value = BitmapComboBox(panel, -1, choices=[], size=(160, -1), style=wx.CB_READONLY)

        # add choices
        self.plot_palette_value.Append("HLS", bitmap=self._colormaps.cmap_hls)
        self.plot_palette_value.Append("HUSL", bitmap=self._colormaps.cmap_husl)
        self.plot_palette_value.Append("Cubehelix", bitmap=self._colormaps.cmap_cubehelix)
        self.plot_palette_value.Append("Spectral", bitmap=self._colormaps.cmap_spectral)
        self.plot_palette_value.Append("Viridis", bitmap=self._colormaps.cmap_viridis)
        self.plot_palette_value.Append("Rainbow", bitmap=self._colormaps.cmap_rainbow)
        self.plot_palette_value.Append("Inferno", bitmap=self._colormaps.cmap_inferno)
        self.plot_palette_value.Append("Cividis", bitmap=self._colormaps.cmap_cividis)
        self.plot_palette_value.Append("Winter", bitmap=self._colormaps.cmap_winter)
        self.plot_palette_value.Append("Cool", bitmap=self._colormaps.cmap_cool)
        self.plot_palette_value.Append("Gray", bitmap=self._colormaps.cmap_gray)
        self.plot_palette_value.Append("RdPu", bitmap=self._colormaps.cmap_rdpu)
        self.plot_palette_value.Append("Tab20b", bitmap=self._colormaps.cmap_tab20b)
        self.plot_palette_value.Append("Tab20c", bitmap=self._colormaps.cmap_tab20c)

        self.plot_palette_value.SetStringSelection(CONFIG.currentPalette)
        self.plot_palette_value.Bind(wx.EVT_COMBOBOX, self.on_change_color_palette)

        # axes parameters
        axis_grid = wx.GridBagSizer(2, 2)
        n = 0
        axis_grid.Add(plot_axis_on_off, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot_axis_on_off_check, (n, 1), flag=wx.EXPAND)
        n += 1
        axis_grid.Add(plot_spines, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot_left_spines_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_right_spines_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_top_spines_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_bottom_spines_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(plot_ticks_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot_left_ticks_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_right_ticks_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_top_ticks_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_bottom_ticks_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(plot_tick_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot_left_tick_labels_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_right_tick_labels_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_top_tick_labels_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.plot_bottom_tick_labels_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(plot_frame_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot_frame_width_value, (n, 1), (1, 2), flag=wx.ALIGN_CENTER)

        # font parameters
        font_grid = wx.GridBagSizer(2, 2)
        n = 0
        font_grid.Add(plot_padding, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.plot_padding_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        font_grid.Add(plot_title_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.plot_title_fontsize_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        font_grid.Add(self.plot1d_title_font_weight_check, (n, 3), flag=wx.EXPAND)
        n += 1
        font_grid.Add(plot_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.plot_label_fontsize_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        font_grid.Add(self.plot_label_font_weight_check, (n, 3), flag=wx.EXPAND)
        n += 1
        font_grid.Add(plot_tick_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.plot_tick_fontsize_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        font_grid.Add(self.plot_tick_font_weight_check, (n, 3), flag=wx.EXPAND)
        n += 1
        font_grid.Add(plot_annotation_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.plot_annotation_fontsize_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        font_grid.Add(self.plot_annotation_font_weight_check, (n, 3), flag=wx.EXPAND)

        style_grid = wx.GridBagSizer(2, 2)
        n = 0
        style_grid.Add(style_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        style_grid.Add(self.plot_style_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        style_grid.Add(plot_palette, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        style_grid.Add(self.plot_palette_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        axis_parameters_label = wx.StaticText(panel, -1, "Axis and frame parameters")
        set_item_font(axis_parameters_label)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        font_parameters_label = wx.StaticText(panel, -1, "Font and label parameters")
        set_item_font(font_parameters_label)

        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        style_parameters_label = wx.StaticText(panel, -1, "Style parameters")
        set_item_font(style_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(axis_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(axis_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(font_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(font_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(style_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(style_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_plot_sizes(self, panel):
        """Make plot size panel"""

        general_plot_name = wx.StaticText(panel, -1, "Plot name:")
        self.general_plot_name_value = wx.Choice(
            panel, -1, choices=sorted(CONFIG._plotSettings.keys()), size=(-1, -1)  # noqa
        )
        self.general_plot_name_value.SetSelection(0)
        self.general_plot_name_value.Bind(wx.EVT_CHOICE, self.on_update_plot_sizes)

        plot_size_label = wx.StaticText(panel, -1, "Plot size (proportion)")

        left_label = wx.StaticText(panel, -1, "Left")
        self.general_left_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_left_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        bottom_label = wx.StaticText(panel, -1, "Bottom")
        self.general_bottom_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_bottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        width_label = wx.StaticText(panel, -1, "Width")
        self.general_width_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        height_label = wx.StaticText(panel, -1, "Height")
        self.general_height_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        plot_size_inch = wx.StaticText(panel, -1, "Plot size (inch)")

        general_width_inch_value = wx.StaticText(panel, -1, "Width (inch)")
        self.general_width_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0, max=20, initial=0, inc=2, size=(60, -1)
        )
        self.general_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        general_height_inch_value = wx.StaticText(panel, -1, "Height (inch)")
        self.general_height_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=20, initial=0, inc=2, size=(60, -1)
        )
        self.general_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        # add elements to grids
        axes_grid = wx.GridBagSizer(2, 2)
        n = 0
        axes_grid.Add(general_plot_name, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_plot_name_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        axes_grid.Add(plot_size_label, (n, 0), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        n += 1
        axes_grid.Add(left_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_left_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        axes_grid.Add(bottom_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_bottom_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        axes_grid.Add(width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_width_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        axes_grid.Add(height_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_height_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        axes_grid.Add(plot_size_inch, (n, 0), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        n += 1
        axes_grid.Add(general_width_inch_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_width_inch_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        axes_grid.Add(general_height_inch_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_height_inch_value, (n, 1), flag=wx.ALIGN_LEFT)

        axes_parameters_label = wx.StaticText(panel, -1, "Axes parameters")
        set_item_font(axes_parameters_label)

        # add elements to the main grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(axes_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(axes_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_ui_behaviour(self, panel):
        """Make UI behaviour panel"""
        zoom_extract_crossover_1d_label = wx.StaticText(panel, -1, "Crossover (1D):")
        self.zoom_extract_crossover_1d_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG._plots_extract_crossover_1D),  # noqa
            min=0.01,
            max=1,
            initial=0,
            inc=0.01,
            size=(CTRL_SIZE, -1),
        )
        self.zoom_extract_crossover_1d_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_zoom)

        zoom_extract_crossover_2d_label = wx.StaticText(panel, -1, "Crossover (2D):")
        self.zoom_extract_crossover_2d_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG._plots_extract_crossover_2D),  # noqa
            min=0.001,
            max=1,
            initial=0,
            inc=0.01,
            size=(CTRL_SIZE, -1),
        )
        self.zoom_extract_crossover_2d_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_zoom)

        zoom_zoom_vertical_color_label = wx.StaticText(panel, -1, "Drag color (vertical):")
        self.zoom_zoom_vertical_color_btn = wx.Button(
            panel, ID_extraSettings_verticalColor, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.zoom_zoom_vertical_color_btn.SetBackgroundColour(
            convert_rgb_1_to_255(CONFIG._plots_zoom_vertical_color)  # noqa
        )
        self.zoom_zoom_vertical_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        zoom_zoom_horizontal_color_label = wx.StaticText(panel, -1, "Drag color (horizontal):")
        self.zoom_zoom_horizontal_color_btn = wx.Button(
            panel, ID_extraSettings_horizontalColor, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.zoom_zoom_horizontal_color_btn.SetBackgroundColour(
            convert_rgb_1_to_255(CONFIG._plots_zoom_horizontal_color)  # noqa
        )
        self.zoom_zoom_horizontal_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        zoom_zoom_box_color_label = wx.StaticText(panel, -1, "Drag color (rectangle):")
        self.zoom_zoom_box_color_btn = wx.Button(
            panel, ID_extraSettings_boxColor, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.zoom_zoom_box_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG._plots_zoom_box_color))  # noqa
        self.zoom_zoom_box_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        zoom_sensitivity_label = wx.StaticText(panel, -1, "Zoom crossover:")
        self.zoom_sensitivity_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG._plots_zoom_crossover),  # noqa
            min=0.01,
            max=1,
            initial=0,
            inc=0.01,
            size=(CTRL_SIZE, -1),
        )
        self.zoom_sensitivity_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_zoom)

        self.general_log_to_file_check = make_checkbox(panel, "Log events to file", evt_id=ID_extraSettings_logging)
        self.general_log_to_file_check.SetValue(CONFIG.logging)
        self.general_log_to_file_check.Bind(wx.EVT_CHECKBOX, self.on_update_states)

        self.general_auto_save_check = make_checkbox(
            panel, "Auto-save settings", evt_id=ID_extraSettings_autoSaveSettings
        )
        self.general_auto_save_check.SetValue(CONFIG.autoSaveSettings)
        self.general_auto_save_check.Bind(wx.EVT_CHECKBOX, self.on_update_states)

        plot_grid = wx.GridBagSizer(2, 2)
        n = 0
        plot_grid.Add(zoom_extract_crossover_1d_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_crossover_1d_value, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        plot_grid.Add(zoom_extract_crossover_2d_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_crossover_2d_value, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_LEFT)
        n += 1
        plot_grid.Add(zoom_zoom_vertical_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_vertical_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        plot_grid.Add(zoom_zoom_horizontal_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_horizontal_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        plot_grid.Add(zoom_zoom_box_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_box_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        plot_grid.Add(zoom_sensitivity_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_sensitivity_value, (n, 1), flag=wx.EXPAND)

        gui_grid = wx.GridBagSizer(2, 2)
        n = 0
        gui_grid.Add(self.general_log_to_file_check, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        gui_grid.Add(self.general_auto_save_check, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)

        usage_parameters_label = wx.StaticText(panel, -1, "In-plot interactivity parameters")
        set_item_font(usage_parameters_label)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        ui_parameters_label = wx.StaticText(panel, -1, "Graphical User Interface parameters")
        set_item_font(ui_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(usage_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(ui_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(gui_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_rmsd(self, panel):
        """Make RMSD/RMSF/Matrix panel"""

        rmsd_position_label = wx.StaticText(panel, -1, "Position:")
        self.rmsd_position_value = wx.Choice(panel, -1, choices=CONFIG.rmsd_position_choices, size=(-1, -1))
        self.rmsd_position_value.SetStringSelection(CONFIG.rmsd_position)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self._recalculate_rmsd_position)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_rmsd)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_apply_rmsd)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_update_rmsd_label)

        rmsd_x_position = wx.StaticText(panel, -1, "Position X:")
        self.rmsd_x_position_value = wx.SpinCtrlDouble(
            panel, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1)
        )
        self.rmsd_x_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._recalculate_rmsd_position)
        self.rmsd_x_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        rmsd_y_position = wx.StaticText(panel, -1, "Position Y:")
        self.rmsd_y_position_value = wx.SpinCtrlDouble(
            panel, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1)
        )
        self.rmsd_y_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._recalculate_rmsd_position)
        self.rmsd_y_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        rmsd_fontsize = wx.StaticText(panel, -1, "Label size:")
        self.rmsd_fontsize_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.rmsd_fontSize), min=1, max=50, initial=0, inc=1, size=(90, -1)
        )
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_rmsd_label)

        self.rmsd_font_weight_check = make_checkbox(panel, "Bold")
        self.rmsd_font_weight_check.SetValue(CONFIG.rmsd_fontWeight)
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_rmsd)
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_rmsd_label)

        rmsd_color_label = wx.StaticText(panel, -1, "Label color:")
        self.rmsd_color_btn = wx.Button(
            panel, ID_extraSettings_labelColor_rmsd, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.rmsd_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_color))
        self.rmsd_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_line_width = wx.StaticText(panel, -1, "Line width:")
        self.rmsd_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.lineWidth_1D * 10),
            min=1,
            max=100,
            initial=CONFIG.rmsd_lineWidth * 10,
            inc=5,
            size=(90, -1),
            name="rmsf",
        )
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        rmsd_line_color = wx.StaticText(panel, -1, "Line color:")
        self.rmsd_color_line_btn = wx.Button(
            panel, ID_extraSettings_lineColor_rmsd, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.rmsd_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_lineColour))
        self.rmsd_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_line_style = wx.StaticText(panel, -1, "Line style:")
        self.rmsd_line_style_value = wx.Choice(panel, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="rmsf")
        self.rmsd_line_style_value.SetStringSelection(CONFIG.rmsd_lineStyle)
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply_rmsd)
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        rmsd_line_hatch = wx.StaticText(panel, -1, "Underline hatch:")
        self.rmsd_line_hatch_value = wx.Choice(
            panel, -1, choices=list(CONFIG.lineHatchDict.keys()), size=(-1, -1), name="rmsf"
        )
        self.rmsd_line_hatch_value.SetStringSelection(
            list(CONFIG.lineHatchDict.keys())[list(CONFIG.lineHatchDict.values()).index(CONFIG.rmsd_lineHatch)]
        )
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_apply_rmsd)
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        rmsd_underline_color = wx.StaticText(panel, -1, "Underline color:")
        self.rmsd_underline_color_btn = wx.Button(
            panel, ID_extraSettings_underlineColor_rmsd, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.rmsd_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_underlineColor))
        self.rmsd_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_alpha_label = wx.StaticText(panel, -1, "Underline transparency:")
        self.rmsd_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.rmsd_underlineTransparency * 100),
            min=0,
            max=100,
            initial=CONFIG.rmsd_underlineTransparency * 100,
            inc=5,
            size=(90, -1),
            name="rmsf",
        )
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        rmsd_hspace_label = wx.StaticText(panel, -1, "Vertical spacing:")
        self.rmsd_vspace_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.rmsd_hspace),
            min=0,
            max=1,
            initial=CONFIG.rmsd_hspace,
            inc=0.05,
            size=(90, -1),
            name="rmsf.spacing",
        )
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)
        set_tooltip(self.rmsd_vspace_value, "Vertical spacing between RMSF and heatmap plot.")

        rmsd_x_rotation = wx.StaticText(panel, -1, "Tick rotation (x-axis):")
        self.rmsd_x_rotation_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.rmsd_rotation_X),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_label_rmsd_matrix)

        rmsd_y_rotation = wx.StaticText(panel, -1, "Tick rotation (y-axis):")
        self.rmsd_y_rotation_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.rmsd_rotation_Y),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_label_rmsd_matrix)

        rmsd_add_labels_label = wx.StaticText(panel, -1, "Show RMSD labels:")
        self.rmsd_add_labels_check = make_checkbox(panel, "", name="rmsd_matrix")
        self.rmsd_add_labels_check.SetValue(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_rmsd)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update_label_rmsd_matrix)

        rmsd_matrix_fontsize = wx.StaticText(panel, -1, "Label font size:")
        self.rmsd_matrix_fontsize = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.labelFontSize_1D),
            min=0,
            max=48,
            initial=CONFIG.labelFontSize_1D,
            inc=2,
            size=(90, -1),
            name="rmsd_matrix",
        )
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_rmsd)
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        self.rmsd_matrix_font_weight_check = make_checkbox(panel, "Bold", name="rmsd_matrix")
        self.rmsd_matrix_font_weight_check.SetValue(CONFIG.labelFontWeight_1D)
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_rmsd)
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        rmsd_matrix_color_fmt = wx.StaticText(panel, -1, "Color formatter:")
        self.rmsd_matrix_color_fmt = wx.Choice(
            panel, -1, choices=CONFIG.rmsd_matrix_font_color_choices, size=(-1, -1), name="rmsd_matrix_formatter"
        )
        self.rmsd_matrix_color_fmt.SetStringSelection(CONFIG.rmsd_matrix_font_color_choice)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_apply_rmsd)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_toggle_controls_rmsd)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_update_2d)

        rmsd_matrix_font_color = wx.StaticText(panel, -1, "Labels color:")
        self.rmsd_matrix_font_color_btn = wx.Button(
            panel, -1, "", wx.DefaultPosition, wx.Size(26, 26), name="rmsd_matrix_label"
        )
        self.rmsd_matrix_font_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_matrix_font_color))
        self.rmsd_matrix_font_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_grid = wx.GridBagSizer(2, 2)
        n = 0
        rmsd_grid.Add(rmsd_position_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_grid.Add(rmsd_x_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_x_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_grid.Add(rmsd_y_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_y_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_grid.Add(rmsd_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_fontsize_value, (n, 1), flag=wx.EXPAND)
        rmsd_grid.Add(self.rmsd_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        rmsd_grid.Add(rmsd_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_color_btn, (n, 1), flag=wx.EXPAND)

        rmsf_grid = wx.GridBagSizer(2, 2)
        n = 0
        rmsf_grid.Add(rmsd_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_color_line_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_line_style_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_line_hatch, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_line_hatch_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_underline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_underline_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsf_grid.Add(rmsd_hspace_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_vspace_value, (n, 1), flag=wx.EXPAND)

        rmsd_matrix_grid = wx.GridBagSizer(2, 2)
        n = 0
        rmsd_matrix_grid.Add(rmsd_x_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_x_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_matrix_grid.Add(rmsd_y_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_y_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_matrix_grid.Add(rmsd_add_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_add_labels_check, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_matrix_grid.Add(rmsd_matrix_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_matrix_fontsize, (n, 1), flag=wx.EXPAND)
        rmsd_matrix_grid.Add(self.rmsd_matrix_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        rmsd_matrix_grid.Add(rmsd_matrix_color_fmt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_matrix_color_fmt, (n, 1), flag=wx.EXPAND)
        n += 1
        rmsd_matrix_grid.Add(rmsd_matrix_font_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_matrix_font_color_btn, (n, 1), flag=wx.EXPAND)

        # put it all together
        rmsd_parameters_label = wx.StaticText(panel, -1, "RMSD parameters")
        set_item_font(rmsd_parameters_label)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        rmsf_parameters_label = wx.StaticText(panel, -1, "RMSF parameters")
        set_item_font(rmsf_parameters_label)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        matrix_parameters_label = wx.StaticText(panel, -1, "RMSD matrix parameters")
        set_item_font(matrix_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsd_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(matrix_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_violin(self, panel):
        """Make violin panel"""
        # make elements
        violin_n_limit_label = wx.StaticText(panel, -1, "Violin limit:")
        self.violin_n_limit_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.violin_nlimit),
            min=1,
            max=200,
            initial=CONFIG.violin_nlimit,
            inc=5,
            size=(90, -1),
            name="shade",
        )
        self.violin_n_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)
        self.violin_n_limit_value.SetToolTip("Maximum number of signals before we plot the data as a waterfall plot.")

        violin_orientation_label = wx.StaticText(panel, -1, "Violin plot orientation:")
        self.violin_orientation_value = wx.Choice(
            panel, -1, choices=CONFIG.violin_orientation_choices, size=(-1, -1), name="style"
        )
        self.violin_orientation_value.SetStringSelection(CONFIG.violin_orientation)
        self.violin_orientation_value.Bind(wx.EVT_CHOICE, self.on_apply_violin)

        violin_spacing_label = wx.StaticText(panel, -1, "Spacing:")
        self.violin_spacing_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.violin_spacing), min=0.0, max=5, initial=0, inc=0.25, size=(90, -1)
        )
        self.violin_spacing_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)

        violin_min_percentage_label = wx.StaticText(panel, -1, "Noise threshold:")
        self.violin_min_percentage_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.violin_min_percentage),
            min=0.0,
            max=1.0,
            initial=0,
            inc=0.01,
            size=(90, -1),
            name="data",
        )
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)
        self.violin_min_percentage_value.SetToolTip(
            "Minimal intensity of data to be shown on the plot. Low intensity or sparse datasets can lead"
            " to plot distortions"
        )

        violin_normalize_label = wx.StaticText(panel, -1, "Normalize:")
        self.violin_normalize_check = make_checkbox(panel, "")
        self.violin_normalize_check.SetValue(CONFIG.violin_normalize)
        self.violin_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_apply_violin)

        violin_line_width = wx.StaticText(panel, -1, "Line width:")
        self.violin_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.violin_lineWidth),
            min=1,
            max=10,
            initial=CONFIG.violin_lineWidth,
            inc=1,
            size=(90, -1),
            name="style",
        )
        self.violin_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)
        self.violin_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        violin_line_style = wx.StaticText(panel, -1, "Line style:")
        self.violin_line_style_value = wx.Choice(panel, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="style")
        self.violin_line_style_value.SetStringSelection(CONFIG.violin_lineStyle)
        self.violin_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply_violin)
        self.violin_line_style_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        violin_line_color = wx.StaticText(panel, -1, "Line color:")
        self.violin_color_line_btn = wx.Button(
            panel, ID_extraSettings_lineColour_violin, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="color"
        )
        self.violin_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.violin_color))
        self.violin_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.violin_line_same_as_fill_check = make_checkbox(panel, "Same as fill", name="color")
        self.violin_line_same_as_fill_check.SetValue(CONFIG.violin_line_sameAsShade)
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_apply_violin)
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_violin)
        self.violin_line_same_as_fill_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        violin_color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.violin_colorScheme_value = wx.Choice(
            panel, -1, choices=CONFIG.waterfall_color_choices, size=(-1, -1), name="color"
        )
        self.violin_colorScheme_value.SetStringSelection(CONFIG.violin_color_value)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_apply_violin)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_update_2d)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_violin)

        self.violin_color_scheme_msg = wx.StaticText(panel, -1, "")

        cmap_list = CONFIG.cmaps2[:]
        cmap_list.remove("jet")
        violin_colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.violin_colormap_value = wx.Choice(panel, -1, choices=cmap_list, size=(-1, -1), name="color")
        self.violin_colormap_value.SetStringSelection(CONFIG.violin_colormap)
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply_violin)
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        violin_shade_color_label = wx.StaticText(panel, -1, "Shade color:")
        self.violin_color_fill_btn = wx.Button(
            panel, ID_extraSettings_shadeColour_violin, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="color"
        )
        self.violin_color_fill_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.violin_shade_under_color))
        self.violin_color_fill_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        violin_shade_transparency_label = wx.StaticText(panel, -1, "Shade transparency:")
        self.violin_fill_transparency_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.violin_shade_under_transparency),
            min=0,
            max=1,
            initial=CONFIG.violin_shade_under_transparency,
            inc=0.25,
            size=(90, -1),
            name="shade",
        )
        self.violin_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)
        self.violin_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        violin_label_format_label = wx.StaticText(panel, -1, "Label format:")
        self.violin_label_format_value = wx.Choice(
            panel, -1, choices=CONFIG.violin_label_format_choices, size=(-1, -1), name="label"
        )
        self.violin_label_format_value.SetStringSelection(CONFIG.waterfall_label_format)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_apply_violin)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_update_2d)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_violin)

        violin_label_frequency_label = wx.StaticText(panel, -1, "Label frequency:")
        self.violin_label_frequency_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.violin_labels_frequency),
            min=0,
            max=100,
            initial=CONFIG.violin_labels_frequency,
            inc=1,
            size=(45, -1),
            name="label",
        )
        self.violin_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_violin)

        plot_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot_grid.Add(violin_n_limit_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_n_limit_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_orientation_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_orientation_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_spacing_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_spacing_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_min_percentage_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_min_percentage_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_normalize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_normalize_check, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_line_width, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_line_width_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_line_style, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_line_style_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_line_color, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_line_same_as_fill_check, (y, 1), flag=wx.EXPAND)
        plot_grid.Add(self.violin_color_line_btn, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        plot_grid.Add(violin_color_scheme_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_colorScheme_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_colormap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_colormap_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_shade_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_color_fill_btn, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(violin_shade_transparency_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.violin_fill_transparency_value, (y, 1), flag=wx.EXPAND)

        label_grid = wx.GridBagSizer(2, 2)
        y = 0
        label_grid.Add(violin_label_frequency_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.violin_label_frequency_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(violin_label_format_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.violin_label_format_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(self.violin_color_scheme_msg, (y, 0), (2, 3), flag=wx.EXPAND)

        plot_parameters_label = wx.StaticText(panel, -1, "Plot parameters")
        set_item_font(plot_parameters_label)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        labels_parameters_label = wx.StaticText(panel, -1, "Labels parameters")
        set_item_font(labels_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(labels_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(label_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_waterfall(self, panel):
        """Make waterfall panel"""
        waterfall_offset_label = wx.StaticText(panel, -1, "Offset:")
        self.waterfall_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_offset),
            min=0.0,
            max=1,
            initial=0,
            inc=0.05,
            size=(90, -1),
            name="data",
        )
        self.waterfall_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_increment_label = wx.StaticText(panel, -1, "Increment:")
        self.waterfall_increment_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_increment),
            min=0.0,
            max=99999.0,
            initial=0,
            inc=0.1,
            size=(90, -1),
            name="data",
        )
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_normalize_label = wx.StaticText(panel, -1, "Normalize:")
        self.waterfall_normalize_check = make_checkbox(panel, "", name="data")
        self.waterfall_normalize_check.SetValue(CONFIG.waterfall_normalize)
        self.waterfall_normalize_check.Bind(wx.EVT_CHECKBOX, self.on_apply_waterfall)
        self.waterfall_normalize_check.SetToolTip(
            "Controls whether signals are normalized during plotting. Changing this value will not have immediate"
            " effect until the plot is fully replotted."
        )

        waterfall_reverse_label = wx.StaticText(panel, -1, "Reverse order:")
        self.waterfall_reverse_check = make_checkbox(panel, "", name="data")
        self.waterfall_reverse_check.SetValue(CONFIG.waterfall_reverse)
        self.waterfall_reverse_check.Bind(wx.EVT_CHECKBOX, self.on_apply_waterfall)
        self.waterfall_reverse_check.SetToolTip(
            "Controls in which order lines are plotted. Changing this value will not have immediate"
            " effect until the plot is fully replotted."
        )

        waterfall_line_width_label = wx.StaticText(panel, -1, "Line width:")
        self.waterfall_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_lineWidth),
            min=1,
            max=10,
            initial=CONFIG.waterfall_lineWidth,
            inc=1,
            size=(90, -1),
            name="style",
        )
        self.waterfall_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_line_style_label = wx.StaticText(panel, -1, "Line style:")
        self.waterfall_line_style_value = wx.Choice(
            panel, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="style"
        )
        self.waterfall_line_style_value.SetStringSelection(CONFIG.waterfall_lineStyle)
        self.waterfall_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply_waterfall)
        self.waterfall_line_style_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        waterfall_line_color_label = wx.StaticText(panel, -1, "Line color:")
        self.waterfall_color_line_btn = wx.Button(
            panel, ID_extraSettings_lineColour_waterfall, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="color"
        )
        self.waterfall_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.waterfall_color))
        self.waterfall_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.waterfall_line_sameAsShade_check = make_checkbox(panel, "Same as fill", name="color")
        self.waterfall_line_sameAsShade_check.SetValue(CONFIG.waterfall_line_sameAsShade)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_apply_waterfall)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_waterfall)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        waterfall_shade_under_label = wx.StaticText(panel, -1, "Fill under the curve:")
        self.waterfall_fill_under_check = make_checkbox(panel, "", name="shade")
        self.waterfall_fill_under_check.SetValue(CONFIG.waterfall_shade_under)
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_apply_waterfall)
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_waterfall)
        self.waterfall_fill_under_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        waterfall_color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.waterfall_colorScheme_value = wx.Choice(
            panel, -1, choices=CONFIG.waterfall_color_choices, size=(-1, -1), name="color"
        )
        self.waterfall_colorScheme_value.SetStringSelection(CONFIG.waterfall_color_value)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_apply_waterfall)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_update_2d)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_waterfall)

        cmap_list = CONFIG.cmaps2[:]
        cmap_list.remove("jet")
        waterfall_colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.waterfall_colormap_value = wx.Choice(panel, -1, choices=cmap_list, size=(-1, -1), name="color")
        self.waterfall_colormap_value.SetStringSelection(CONFIG.waterfall_colormap)
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply_waterfall)
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        waterfall_shade_color_label = wx.StaticText(panel, -1, "Fill color:")
        self.waterfall_color_fill_btn = wx.Button(
            panel, ID_extraSettings_shadeColour_waterfall, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="color"
        )
        self.waterfall_color_fill_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.waterfall_shade_under_color))
        self.waterfall_color_fill_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        waterfall_shade_transparency_label = wx.StaticText(panel, -1, "Fill transparency:")
        self.waterfall_fill_transparency_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_shade_under_transparency),
            min=0,
            max=1,
            initial=CONFIG.waterfall_shade_under_transparency,
            inc=0.25,
            size=(90, -1),
            name="shade",
        )
        self.waterfall_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_fill_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_shade_limit_label = wx.StaticText(panel, -1, "Fill limit:")
        self.waterfall_fill_n_limit_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_shade_under_nlimit),
            min=0,
            max=100,
            initial=CONFIG.waterfall_shade_under_nlimit,
            inc=25,
            size=(90, -1),
            name="shade",
        )
        self.waterfall_fill_n_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_fill_n_limit_value.SetToolTip(
            "Maximum number of items to be considered for fill-in plotting. If the number is very high, plotting"
            + " can be slow"
        )

        waterfall_show_labels_label = wx.StaticText(panel, -1, "Show labels:")
        self.waterfall_showLabels_check = make_checkbox(panel, "", name="label")
        self.waterfall_showLabels_check.SetValue(CONFIG.waterfall_add_labels)
        self.waterfall_showLabels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_waterfall)
        self.waterfall_showLabels_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        waterfall_label_frequency_label = wx.StaticText(panel, -1, "Label frequency:")
        self.waterfall_label_frequency_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_labels_frequency),
            min=0,
            max=100,
            initial=CONFIG.waterfall_labels_frequency,
            inc=1,
            size=(45, -1),
            name="label.frequency",
        )
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_label_format_label = wx.StaticText(panel, -1, "Label format:")
        self.waterfall_label_format_value = wx.Choice(
            panel, -1, choices=CONFIG.waterfall_label_format_choices, size=(-1, -1), name="label"
        )
        self.waterfall_label_format_value.SetStringSelection(CONFIG.waterfall_label_format)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_apply_waterfall)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_update_2d)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_waterfall)

        waterfall_label_font_size_label = wx.StaticText(panel, -1, "Font size:")
        self.waterfall_label_font_size_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_label_fontSize),
            min=4,
            max=32,
            initial=CONFIG.waterfall_label_fontSize,
            inc=2,
            size=(45, -1),
            name="label",
        )
        self.waterfall_label_font_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_label_font_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        self.waterfall_label_font_weight_check = make_checkbox(panel, "Bold", name="label")
        self.waterfall_label_font_weight_check.SetValue(CONFIG.waterfall_label_fontWeight)
        self.waterfall_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_waterfall)
        self.waterfall_label_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_2d)

        waterfall_label_x_offset_label = wx.StaticText(panel, -1, "Horizontal offset:")
        self.waterfall_label_x_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_labels_x_offset),
            min=0,
            max=1,
            initial=CONFIG.waterfall_labels_x_offset,
            inc=0.01,
            size=(45, -1),
            name="label",
        )
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        waterfall_label_y_offset_label = wx.StaticText(panel, -1, "Vertical offset:")
        self.waterfall_label_y_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.waterfall_labels_y_offset),
            min=0,
            max=1,
            initial=CONFIG.waterfall_labels_y_offset,
            inc=0.05,
            size=(45, -1),
            name="label",
        )
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_waterfall)
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        self.waterfall_colorScheme_msg = wx.StaticText(panel, -1, "")

        plot_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot_grid.Add(waterfall_offset_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_offset_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_increment_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_increment_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_normalize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_normalize_check, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_reverse_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_reverse_check, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_line_width_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_line_width_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_line_style_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_line_style_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_line_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_line_sameAsShade_check, (y, 1), flag=wx.EXPAND)
        plot_grid.Add(self.waterfall_color_line_btn, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        plot_grid.Add(waterfall_shade_under_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_fill_under_check, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_color_scheme_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_colorScheme_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_colormap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_colormap_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_shade_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_color_fill_btn, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_shade_transparency_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_fill_transparency_value, (y, 1), flag=wx.EXPAND)
        y += 1
        plot_grid.Add(waterfall_shade_limit_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot_grid.Add(self.waterfall_fill_n_limit_value, (y, 1), flag=wx.EXPAND)

        label_grid = wx.GridBagSizer(2, 2)
        y = 0
        label_grid.Add(waterfall_show_labels_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_showLabels_check, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(waterfall_label_frequency_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_label_frequency_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(waterfall_label_format_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_label_format_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(waterfall_label_font_size_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_label_font_size_value, (y, 1), flag=wx.EXPAND)
        label_grid.Add(self.waterfall_label_font_weight_check, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        label_grid.Add(waterfall_label_x_offset_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_label_x_offset_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(waterfall_label_y_offset_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        label_grid.Add(self.waterfall_label_y_offset_value, (y, 1), flag=wx.EXPAND)
        y += 1
        label_grid.Add(self.waterfall_colorScheme_msg, (y, 0), (2, 3), flag=wx.EXPAND)

        plot_parameters_label = wx.StaticText(panel, -1, "Plot parameters")
        set_item_font(plot_parameters_label)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        labels_parameters_label = wx.StaticText(panel, -1, "Labels parameters")
        set_item_font(labels_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(plot_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(labels_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(label_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_colorbar(self, panel):
        """Make colorbar controls"""

        # make elements
        colorbar_tgl = wx.StaticText(panel, -1, "Colorbar:")
        self.colorbar_tgl = make_toggle_btn(panel, "Off", wx.RED, name="colorbar")
        self.colorbar_tgl.SetValue(CONFIG.colorbar)
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_controls_colorbar)
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_apply_colorbar)
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_update_2d)

        colorbar_label_format = wx.StaticText(panel, -1, "Label format:")
        self.colorbar_label_format = wx.Choice(
            panel, -1, choices=CONFIG.colorbar_fmt_choices, size=(-1, -1), name="colorbar"
        )
        self.colorbar_label_format.SetStringSelection(CONFIG.colorbar_fmt)
        self.colorbar_label_format.Bind(wx.EVT_CHOICE, self.on_apply_colorbar)
        self.colorbar_label_format.Bind(wx.EVT_CHOICE, self.on_update_2d)

        colorbar_position = wx.StaticText(panel, -1, "Position:")
        self.colorbar_position_value = wx.Choice(
            panel, -1, choices=CONFIG.colorbar_position_choices, size=(-1, -1), name="colorbar"
        )
        self.colorbar_position_value.SetStringSelection(CONFIG.colorbarPosition)
        self.colorbar_position_value.Bind(wx.EVT_CHOICE, self.on_apply_colorbar)
        self.colorbar_position_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        colorbar_pad = wx.StaticText(panel, -1, "Distance:")
        self.colorbar_pad_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.colorbarPad),
            min=0.0,
            max=2,
            initial=0,
            inc=0.05,
            size=(90, -1),
            name="colorbar",
        )
        self.colorbar_pad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)
        self.colorbar_pad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        colorbar_width = wx.StaticText(panel, -1, "Width (H) / Height (V) (%):")
        self.colorbar_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.colorbarWidth),
            min=0.0,
            max=100,
            initial=0,
            inc=0.5,
            size=(90, -1),
            name="colorbar",
        )
        self.colorbar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)
        self.colorbar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        colorbar_fontsize = wx.StaticText(panel, -1, "Label font size:")
        self.colorbar_fontsize_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.colorbarLabelSize),
            min=0,
            max=32,
            initial=0,
            inc=2,
            size=(90, -1),
            name="colorbar",
        )
        self.colorbar_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)
        self.colorbar_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        colorbar_label_color = wx.StaticText(panel, -1, "Label color:")
        self.colorbar_label_color_btn = wx.Button(
            panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0.0, name="colorbar.label"
        )
        self.colorbar_label_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.colorbar_label_color))
        self.colorbar_label_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        colorbar_outline_color = wx.StaticText(panel, -1, "Outline color:")
        self.colorbar_outline_color_btn = wx.Button(
            panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="colorbar.outline"
        )
        self.colorbar_outline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.colorbar_edge_color))
        self.colorbar_outline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        colorbar_outline_width = wx.StaticText(panel, -1, "Frame width:")
        self.colorbar_outline_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.colorbar_edge_width),
            min=0,
            max=10,
            initial=CONFIG.colorbar_edge_width,
            inc=1,
            size=(90, -1),
            name="colorbar.frame",
        )
        self.colorbar_outline_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)
        self.colorbar_outline_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colorbar_tgl, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_tgl, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_format, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_format, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_pad, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_pad_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_fontsize_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_outline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_outline_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_outline_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_outline_width_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_legend(self, panel):
        """Make legend panel"""
        legend_toggle = wx.StaticText(panel, -1, "Legend:")
        self.legend_toggle = make_toggle_btn(panel, "Off", wx.RED)
        self.legend_toggle.SetValue(CONFIG.legend)
        self.legend_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_controls_legend)

        legend_position = wx.StaticText(panel, -1, "Position:")
        self.legend_position_value = wx.Choice(panel, -1, choices=CONFIG.legendPositionChoice, size=(-1, -1))
        self.legend_position_value.SetStringSelection(CONFIG.legendPosition)
        self.legend_position_value.Bind(wx.EVT_CHOICE, self.on_apply_legend)

        legend_columns = wx.StaticText(panel, -1, "Columns:")
        self.legend_columns_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.legendColumns), min=1, max=5, initial=0, inc=1, size=(90, -1)
        )
        self.legend_columns_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legend_fontsize = wx.StaticText(panel, -1, "Font size:")
        self.legend_fontsize_value = wx.Choice(panel, -1, choices=CONFIG.legendFontChoice, size=(-1, -1))
        self.legend_fontsize_value.SetStringSelection(CONFIG.legendFontSize)
        self.legend_fontsize_value.Bind(wx.EVT_CHOICE, self.on_apply_legend)

        legend_marker_size = wx.StaticText(panel, -1, "Marker size:")
        self.legend_marker_size_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.legendMarkerSize), min=0.5, max=5, initial=0, inc=0.5, size=(90, -1)
        )
        self.legend_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legend_n_markers = wx.StaticText(panel, -1, "Number of points:")
        self.legend_n_markers_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.legendNumberMarkers), min=1, max=10, initial=1, inc=1, size=(90, -1)
        )
        self.legend_n_markers_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legend_marker_before = wx.StaticText(panel, -1, "Marker before label:")
        self.legend_marker_before_check = make_checkbox(panel, "")
        self.legend_marker_before_check.SetValue(CONFIG.legendMarkerFirst)
        self.legend_marker_before_check.Bind(wx.EVT_CHECKBOX, self.on_apply_legend)

        legend_alpha = wx.StaticText(panel, -1, "Frame transparency:")
        self.legend_alpha_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.legendAlpha), min=0.0, max=1, initial=0, inc=0.05, size=(90, -1)
        )
        self.legend_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legend_patch_alpha = wx.StaticText(panel, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.legendPatchAlpha), min=0.0, max=1, initial=0, inc=0.25, size=(90, -1)
        )
        self.legend_patch_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legend_frame_label = wx.StaticText(panel, -1, "Frame:")
        self.legend_frame_check = make_checkbox(panel, "")
        self.legend_frame_check.SetValue(CONFIG.legendFrame)
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.on_apply_legend)

        legend_fancy = wx.StaticText(panel, -1, "Rounded corners:")
        self.legend_fancybox_check = make_checkbox(panel, "")
        self.legend_fancybox_check.SetValue(CONFIG.legendFancyBox)
        self.legend_fancybox_check.Bind(wx.EVT_CHECKBOX, self.on_apply_legend)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(legend_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_toggle, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_columns, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_columns_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_fontsize_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_marker_size_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_n_markers, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_n_markers_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_marker_before, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_marker_before_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_patch_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_patch_alpha_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_frame_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_frame_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_fancy, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.legend_fancybox_check, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_1d(self, panel):
        """Make 1d plot settings panel"""
        plot1d_line_width = wx.StaticText(panel, -1, "Line width:")
        self.plot1d_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.lineWidth_1D * 10),
            min=1,
            max=100,
            initial=CONFIG.lineWidth_1D * 10,
            inc=10,
            size=(90, -1),
        )
        self.plot1d_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)
        self.plot1d_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_1d)

        plot1d_line_color = wx.StaticText(panel, -1, "Line color:")
        self.plot1d_line_color_btn = wx.Button(panel, ID_extraSettings_lineColor_1D, "", size=wx.Size(26, 26))
        self.plot1d_line_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.lineColour_1D))
        self.plot1d_line_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_line_style = wx.StaticText(panel, -1, "Line style:")
        self.plot1d_line_style_value = wx.Choice(panel, -1, choices=CONFIG.lineStylesList, size=(-1, -1))
        self.plot1d_line_style_value.SetStringSelection(CONFIG.lineStyle_1D)
        self.plot1d_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply_1d)
        self.plot1d_line_style_value.Bind(wx.EVT_CHOICE, self.on_update_1d)

        plot1d_underline = wx.StaticText(panel, -1, "Fill under:")
        self.plot1d_underline_check = make_checkbox(panel, "")
        self.plot1d_underline_check.SetValue(CONFIG.lineShadeUnder_1D)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_apply_1d)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_1d)
        self.plot1d_underline_check.Bind(wx.EVT_CHECKBOX, self.on_update_1d)

        plot1d_underline_alpha = wx.StaticText(panel, -1, "Fill transparency:")
        self.plot1d_underline_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.lineShadeUnderTransparency_1D * 100),
            min=0,
            max=100,
            initial=CONFIG.lineShadeUnderTransparency_1D * 100,
            inc=10,
            size=(90, -1),
        )
        self.plot1d_underline_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)
        self.plot1d_underline_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_1d)

        plot1d_underline_color = wx.StaticText(panel, -1, "Fill color:")
        self.plot1d_underline_color_btn = wx.Button(
            panel, ID_extraSettings_shadeUnderColor_1D, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.plot1d_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.lineShadeUnderColour_1D))
        self.plot1d_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_marker_shape = wx.StaticText(panel, -1, "Marker shape:")
        self.plot1d_marker_shape_value = wx.Choice(
            panel, -1, choices=list(CONFIG.markerShapeDict.keys()), size=(-1, -1)
        )
        self.plot1d_marker_shape_value.SetStringSelection(CONFIG.markerShapeTXT_1D)
        self.plot1d_marker_shape_value.Bind(wx.EVT_CHOICE, self.on_apply_1d)

        plot1d_marker_size = wx.StaticText(panel, -1, "Marker size:")
        self.plot1d_marker_size_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.markerSize_1D), min=1, max=100, initial=1, inc=10, size=(90, -1)
        )
        self.plot1d_marker_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)

        plot1d_alpha = wx.StaticText(panel, -1, "Marker transparency:")
        self.plot1d_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.markerTransparency_1D * 100),
            min=0,
            max=100,
            initial=CONFIG.markerTransparency_1D * 100,
            inc=10,
            size=(90, -1),
        )
        self.plot1d_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)

        plot1d_marker_color = wx.StaticText(panel, -1, "Marker face color:")
        self.plot1d_marker_color_btn = wx.Button(
            panel, ID_extraSettings_markerColor_1D, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.plot1d_marker_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.markerColor_1D))
        self.plot1d_marker_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        plot1d_marker_edge_color = wx.StaticText(panel, -1, "Marker edge color:")
        self.plot1d_marker_edge_color_btn = wx.Button(
            panel, ID_extraSettings_edgeMarkerColor_1D, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )

        self.plot1d_marker_edge_color_check = make_checkbox(panel, "Same as fill")
        self.plot1d_marker_edge_color_check.SetValue(CONFIG.markerEdgeUseSame_1D)
        self.plot1d_marker_edge_color_check.Bind(wx.EVT_CHECKBOX, self.on_apply_1d)
        self.plot1d_marker_edge_color_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_1d)

        self.plot1d_marker_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.markerEdgeColor_3D))
        self.plot1d_marker_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        bar_width_label = wx.StaticText(panel, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.bar_width), min=0.01, max=10, inc=0.1, initial=CONFIG.bar_width, size=(90, -1)
        )
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)

        bar_alpha_label = wx.StaticText(panel, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.bar_alpha), min=0, max=1, initial=CONFIG.bar_alpha, inc=0.25, size=(90, -1)
        )
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)

        bar_line_width_label = wx.StaticText(panel, -1, "Bar edge line width:")
        self.bar_line_width_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.bar_lineWidth), min=0, max=5, initial=CONFIG.bar_lineWidth, inc=1, size=(90, -1)
        )
        self.bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_1d)

        bar_edge_color_label = wx.StaticText(panel, -1, "Bar edge color:")
        self.bar_edge_color_btn = wx.Button(
            panel, ID_extraSettings_bar_edgeColor, "", wx.DefaultPosition, wx.Size(26, 26), 0
        )
        self.bar_edge_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.bar_edge_color))
        self.bar_edge_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        self.bar_color_edge_check = make_checkbox(panel, "Same as fill")
        self.bar_color_edge_check.SetValue(CONFIG.bar_sameAsFill)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_apply_1d)
        self.bar_color_edge_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls_1d)

        # Replot button
        self.plot1d_update_btn = wx.Button(panel, wx.ID_ANY, "Update", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.plot1d_update_btn.Bind(wx.EVT_BUTTON, self.on_update_1d)

        self.plot1d_replot_btn = wx.Button(panel, wx.ID_ANY, "Replot", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.plot1d_replot_btn.Bind(wx.EVT_BUTTON, self.on_replot_1d)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.plot1d_update_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.plot1d_replot_btn, (n, 1), flag=wx.EXPAND)

        line_grid = wx.GridBagSizer(2, 2)
        n = 0
        line_grid.Add(plot1d_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_line_width_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        line_grid.Add(plot1d_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_line_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        line_grid.Add(plot1d_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_line_style_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        line_grid.Add(plot1d_underline, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_underline_check, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        line_grid.Add(plot1d_underline_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_underline_alpha_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1

        line_grid.Add(plot1d_underline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1d_underline_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        marker_grid = wx.GridBagSizer(2, 2)
        n = 0
        marker_grid.Add(plot1d_marker_shape, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1d_marker_shape_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        marker_grid.Add(plot1d_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1d_marker_size_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        marker_grid.Add(plot1d_alpha, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1d_alpha_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        marker_grid.Add(plot1d_marker_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1d_marker_color_btn, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        marker_grid.Add(plot1d_marker_edge_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1d_marker_edge_color_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        marker_grid.Add(self.plot1d_marker_edge_color_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        bar_grid = wx.GridBagSizer(2, 2)
        n = 0
        bar_grid.Add(bar_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_width_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        bar_grid.Add(bar_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_alpha_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        bar_grid.Add(bar_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_line_width_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        bar_grid.Add(bar_edge_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_color_edge_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        bar_grid.Add(self.bar_edge_color_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        line_parameters_label = wx.StaticText(panel, -1, "Line parameters")
        set_item_font(line_parameters_label)

        marker_parameters_label = wx.StaticText(panel, -1, "Marker parameters")
        set_item_font(marker_parameters_label)

        barplot_parameters_label = wx.StaticText(panel, -1, "Barplot parameters")
        set_item_font(barplot_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(line_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(line_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(marker_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(marker_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(barplot_parameters_label, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(bar_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_2d(self, panel):
        """Make 2d plot panel"""
        plot2d_plot_type = wx.StaticText(panel, -1, "Plot type:")
        self.plot2d_plot_type_value = wx.Choice(panel, -1, choices=CONFIG.imageType2D, size=(-1, -1))
        self.plot2d_plot_type_value.SetStringSelection(CONFIG.plotType)
        self.plot2d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_apply_2d)
        self.plot2d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_replot_2d)

        plot2d_colormap = wx.StaticText(panel, -1, "Colormap:")
        self.plot2d_colormap_value = wx.Choice(panel, -1, choices=CONFIG.cmaps2, size=(-1, -1), name="color")
        self.plot2d_colormap_value.SetStringSelection(CONFIG.currentCmap)
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply_2d)
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        self.plot2d_override_colormap_check = make_checkbox(panel, "Always use global colormap")
        self.plot2d_override_colormap_check.SetValue(CONFIG.useCurrentCmap)
        self.plot2d_override_colormap_check.Bind(wx.EVT_CHECKBOX, self.on_apply_2d)
        self.plot2d_override_colormap_check.Bind(wx.EVT_CHOICE, self.on_update_2d)

        plot2d_interpolation = wx.StaticText(panel, -1, "Interpolation:")
        self.plot2d_interpolation_value = wx.Choice(panel, -1, choices=CONFIG.comboInterpSelectChoices, size=(-1, -1))
        self.plot2d_interpolation_value.SetStringSelection(CONFIG.interpolation)
        self.plot2d_interpolation_value.Bind(wx.EVT_CHOICE, self.on_apply_2d)
        self.plot2d_interpolation_value.Bind(wx.EVT_CHOICE, self.on_update_2d)

        plot2d_normalization = wx.StaticText(panel, -1, "Normalization:")
        self.plot2d_normalization_value = wx.Choice(
            panel, -1, choices=["Midpoint", "Logarithmic", "Power"], size=(-1, -1), name="normalization"
        )
        self.plot2d_normalization_value.SetStringSelection(CONFIG.normalization_2D)
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_apply_2d)
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_update_2d)
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls_2d)

        plot2d_min = wx.StaticText(panel, -1, "Min %:")
        self.plot2d_min_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.minCmap), min=0, max=100, initial=0, inc=5, size=(50, -1), name="normalization"
        )
        self.plot2d_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_2d)
        self.plot2d_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        plot2d_mid = wx.StaticText(panel, -1, "Mid %:")
        self.plot2d_mid_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.midCmap), min=0, max=100, initial=0, inc=5, size=(50, -1), name="normalization"
        )
        self.plot2d_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_2d)
        self.plot2d_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        plot2d_max = wx.StaticText(panel, -1, "Max %:")
        self.plot2d_max_value = wx.SpinCtrlDouble(
            panel, -1, value=str(CONFIG.maxCmap), min=0, max=100, initial=0, inc=5, size=(90, -1), name="normalization"
        )
        self.plot2d_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_2d)
        self.plot2d_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        plot2d_normalization_gamma = wx.StaticText(panel, -1, "Power gamma:")
        self.plot2d_normalization_gamma_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.normalization_2D_power_gamma),
            min=0,
            max=3,
            initial=0,
            inc=0.1,
            size=(90, -1),
            name="normalization",
        )
        self.plot2d_normalization_gamma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_2d)
        self.plot2d_normalization_gamma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_2d)

        # Replot button
        self.plot2d_update_btn = wx.Button(panel, wx.ID_ANY, "Update")
        self.plot2d_update_btn.Bind(wx.EVT_BUTTON, self.on_update_2d)

        self.plot2d_replot_btn = wx.Button(panel, wx.ID_ANY, "Replot")
        self.plot2d_replot_btn.Bind(wx.EVT_BUTTON, self.on_replot_2d)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.plot2d_update_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.plot2d_replot_btn, (n, 1), flag=wx.EXPAND)

        plot2d_grid = wx.GridBagSizer(2, 2)
        n = 0
        plot2d_grid.Add(plot2d_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot2d_grid.Add(self.plot2d_colormap_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        plot2d_grid.Add(self.plot2d_override_colormap_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        plot2d_grid.Add(plot2d_plot_type, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot2d_grid.Add(self.plot2d_plot_type_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        plot2d_grid.Add(plot2d_interpolation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot2d_grid.Add(self.plot2d_interpolation_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        normalization_grid = wx.GridBagSizer(2, 2)
        n = 0
        normalization_grid.Add(plot2d_normalization, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        normalization_grid.Add(self.plot2d_normalization_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        normalization_grid.Add(plot2d_min, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        normalization_grid.Add(self.plot2d_min_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        normalization_grid.Add(plot2d_mid, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        normalization_grid.Add(self.plot2d_mid_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        normalization_grid.Add(plot2d_max, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        normalization_grid.Add(self.plot2d_max_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        normalization_grid.Add(plot2d_normalization_gamma, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        normalization_grid.Add(self.plot2d_normalization_gamma_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        heatmap_parameters_label = wx.StaticText(panel, -1, "Heatmap parameters")
        set_item_font(heatmap_parameters_label)

        normalization_parameters_label = wx.StaticText(panel, -1, "Normalization parameters")
        set_item_font(normalization_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(heatmap_parameters_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(normalization_parameters_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(normalization_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def make_panel_3d(self, panel):
        """Make 3d plot panel"""
        plot3d_plot_type = wx.StaticText(panel, -1, "Plot type:")
        self.plot3d_plot_type_value = wx.Choice(panel, -1, choices=CONFIG.imageType3D, size=(-1, -1))
        self.plot3d_plot_type_value.SetStringSelection(CONFIG.plotType_3D)
        self.plot3d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_apply_3d)
        self.plot3d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_replot_3d)

        plot3d_shade_toggle = wx.StaticText(panel, -1, "Show shade:")
        self.plot3d_shade_check = make_checkbox(panel, "")
        self.plot3d_shade_check.SetValue(CONFIG.shade_3D)
        self.plot3d_shade_check.Bind(wx.EVT_CHECKBOX, self.on_apply_3d)
        self.plot3d_shade_check.Bind(wx.EVT_CHECKBOX, self.on_update_3d)

        plot3d_grids_toggle = wx.StaticText(panel, -1, "Show grids:")
        self.plot3d_grids_check = make_checkbox(panel, "")
        self.plot3d_grids_check.SetValue(CONFIG.showGrids_3D)
        self.plot3d_grids_check.Bind(wx.EVT_CHECKBOX, self.on_apply_3d)
        self.plot3d_grids_check.Bind(wx.EVT_CHECKBOX, self.on_update_3d)

        plot3d_ticks_toggle = wx.StaticText(panel, -1, "Show ticks:")
        self.plot3d_ticks_check = make_checkbox(panel, "")
        self.plot3d_ticks_check.SetValue(CONFIG.ticks_3D)
        self.plot3d_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_3d)
        self.plot3d_ticks_check.Bind(wx.EVT_CHECKBOX, self.on_replot_3d)

        plot3d_spines_toggle = wx.StaticText(panel, -1, "Show line:")
        self.plot3d_spines_check = make_checkbox(panel, "")
        self.plot3d_spines_check.SetValue(CONFIG.spines_3D)
        self.plot3d_spines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_3d)
        self.plot3d_spines_check.Bind(wx.EVT_CHECKBOX, self.on_replot_3d)

        plot3d_labels_toggle = wx.StaticText(panel, -1, "Show labels:")
        self.plot3d_labels_check = make_checkbox(panel, "")
        self.plot3d_labels_check.SetValue(CONFIG.labels_3D)
        self.plot3d_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_3d)
        self.plot3d_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update_3d)

        # Replot button
        self.plot3d_update_btn = wx.Button(panel, wx.ID_ANY, "Update", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.plot3d_update_btn.Bind(wx.EVT_BUTTON, self.on_update_3d)

        # Replot button
        self.plot3d_replot_btn = wx.Button(panel, wx.ID_ANY, "Replot", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.plot3d_replot_btn.Bind(wx.EVT_BUTTON, self.on_replot_3d)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.plot3d_update_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.plot3d_replot_btn, (n, 1), flag=wx.EXPAND)

        plot3d_grid = wx.GridBagSizer(2, 2)
        n = 0
        plot3d_grid.Add(plot3d_plot_type, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plot3d_grid.Add(self.plot3d_plot_type_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        # axis grids
        axis_grid = wx.GridBagSizer(2, 2)
        n = 0
        axis_grid.Add(plot3d_shade_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3d_shade_check, (n, 1), flag=wx.EXPAND)
        n += 1
        axis_grid.Add(plot3d_grids_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3d_grids_check, (n, 1), flag=wx.EXPAND)
        n += 1
        axis_grid.Add(plot3d_ticks_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3d_ticks_check, (n, 1), flag=wx.EXPAND)
        n += 1
        axis_grid.Add(plot3d_spines_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3d_spines_check, (n, 1), flag=wx.EXPAND)
        n += 1
        axis_grid.Add(plot3d_labels_toggle, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3d_labels_check, (n, 1), flag=wx.EXPAND)

        heatmap_parameters_label = wx.StaticText(panel, -1, "Heatmap parameters")
        set_item_font(heatmap_parameters_label)

        axes_parameters_label = wx.StaticText(panel, -1, "Axis parameters")
        set_item_font(axes_parameters_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(heatmap_parameters_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot3d_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(axes_parameters_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(axis_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_apply_general(self, evt):
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

        if evt is not None:
            evt.Skip()

    def on_apply_1d(self, evt):
        """Update 1d parameters"""
        # plot 1D
        CONFIG.lineWidth_1D = str2num(self.plot1d_line_width_value.GetValue()) / 10
        CONFIG.lineStyle_1D = self.plot1d_line_style_value.GetStringSelection()
        CONFIG.markerSize_1D = str2num(self.plot1d_marker_size_value.GetValue())
        CONFIG.lineShadeUnder_1D = self.plot1d_underline_check.GetValue()
        CONFIG.lineShadeUnderTransparency_1D = str2num(self.plot1d_underline_alpha_value.GetValue()) / 100
        CONFIG.markerShapeTXT_1D = self.plot1d_marker_shape_value.GetStringSelection()
        CONFIG.markerShape_1D = CONFIG.markerShapeDict[self.plot1d_marker_shape_value.GetStringSelection()]
        CONFIG.markerTransparency_1D = str2num(self.plot1d_alpha_value.GetValue()) / 100

        # bar
        CONFIG.bar_width = self.bar_width_value.GetValue()
        CONFIG.bar_alpha = self.bar_alpha_value.GetValue()
        CONFIG.bar_sameAsFill = self.bar_color_edge_check.GetValue()
        CONFIG.bar_lineWidth = self.bar_line_width_value.GetValue()

        if evt is not None:
            evt.Skip()

    def on_apply_2d(self, evt):
        """Update 2d parameters"""
        if self.import_evt:
            return
        CONFIG.normalization_2D = self.plot2d_normalization_value.GetStringSelection()
        CONFIG.currentCmap = self.plot2d_colormap_value.GetStringSelection()
        CONFIG.useCurrentCmap = self.plot2d_override_colormap_check.GetValue()
        CONFIG.plotType = self.plot2d_plot_type_value.GetStringSelection()
        CONFIG.interpolation = self.plot2d_interpolation_value.GetStringSelection()
        CONFIG.minCmap = str2num(self.plot2d_min_value.GetValue())
        CONFIG.midCmap = str2num(self.plot2d_mid_value.GetValue())
        CONFIG.maxCmap = str2num(self.plot2d_max_value.GetValue())
        CONFIG.normalization_2D_power_gamma = str2num(self.plot2d_normalization_gamma_value.GetValue())

        # fire events
        # self.on_apply(evt=None)

        if evt is not None:
            evt.Skip()

    def on_apply_3d(self, evt):
        """Update 3d parameters"""
        if self.import_evt:
            return

        CONFIG.plotType_3D = self.plot3d_plot_type_value.GetStringSelection()
        CONFIG.showGrids_3D = self.plot3d_grids_check.GetValue()
        CONFIG.shade_3D = self.plot3d_shade_check.GetValue()
        CONFIG.ticks_3D = self.plot3d_ticks_check.GetValue()
        CONFIG.spines_3D = self.plot3d_spines_check.GetValue()
        CONFIG.labels_3D = self.plot3d_labels_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_apply_axes(self, evt):
        """Update general parameters"""
        if self.import_evt:
            return

        # general
        plot_name = self.general_plot_name_value.GetStringSelection()
        plot_values = [
            self.general_left_value.GetValue(),
            self.general_bottom_value.GetValue(),
            self.general_width_value.GetValue(),
            self.general_height_value.GetValue(),
        ]
        CONFIG._plotSettings[plot_name]["axes_size"] = plot_values  # noqa

        plot_sizes = [self.general_width_inch_value.GetValue(), self.general_height_inch_value.GetValue()]
        CONFIG._plotSettings[plot_name]["resize_size"] = plot_sizes  # noqa

        # fire events
        self.panel_plot.plot_update_axes(plot_name)

        if evt is not None:
            evt.Skip()

    def on_apply_zoom(self, evt):
        """Apply zoom parameters"""
        if self.import_evt:
            return

        # plots
        CONFIG._plots_zoom_crossover = self.zoom_sensitivity_value.GetValue()
        CONFIG._plots_extract_crossover_1D = self.zoom_extract_crossover_1d_value.GetValue()
        CONFIG._plots_extract_crossover_2D = self.zoom_extract_crossover_2d_value.GetValue()

        # fire events
        self.presenter.view.on_update_interaction_settings(None)

        if evt is not None:
            evt.Skip()

    def on_apply_colorbar(self, evt):
        """Apply colorbar parameters"""
        CONFIG.colorbar = self.colorbar_tgl.GetValue()
        CONFIG.colorbarPosition = self.colorbar_position_value.GetStringSelection()
        CONFIG.colorbarWidth = str2num(self.colorbar_width_value.GetValue())
        CONFIG.colorbarPad = str2num(self.colorbar_pad_value.GetValue())
        CONFIG.colorbarLabelSize = str2num(self.colorbar_fontsize_value.GetValue())
        CONFIG.colorbar_fmt = self.colorbar_label_format.GetStringSelection()
        CONFIG.colorbar_edge_width = str2num(self.colorbar_outline_width_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_apply_legend(self, evt):
        """Apply legend parameters"""
        CONFIG.legend = self.legend_toggle.GetValue()
        CONFIG.legendPosition = self.legend_position_value.GetStringSelection()
        CONFIG.legendColumns = str2int(self.legend_columns_value.GetValue())
        CONFIG.legendFontSize = self.legend_fontsize_value.GetStringSelection()
        CONFIG.legendFrame = self.legend_frame_check.GetValue()
        CONFIG.legendAlpha = str2num(self.legend_alpha_value.GetValue())
        CONFIG.legendMarkerSize = str2num(self.legend_marker_size_value.GetValue())
        CONFIG.legendNumberMarkers = str2int(self.legend_n_markers_value.GetValue())
        CONFIG.legendMarkerFirst = self.legend_marker_before_check.GetValue()
        CONFIG.legendPatchAlpha = self.legend_patch_alpha_value.GetValue()
        CONFIG.legendFancyBox = self.legend_fancybox_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_apply_violin(self, evt):
        """Apply violin parameters"""
        CONFIG.violin_orientation = self.violin_orientation_value.GetStringSelection()
        CONFIG.violin_min_percentage = str2num(self.violin_min_percentage_value.GetValue())
        CONFIG.violin_spacing = str2num(self.violin_spacing_value.GetValue())
        CONFIG.violin_lineWidth = self.violin_line_width_value.GetValue()
        CONFIG.violin_lineStyle = self.violin_line_style_value.GetStringSelection()
        CONFIG.violin_color_scheme = self.violin_colorScheme_value.GetStringSelection()
        if CONFIG.violin_color_scheme == "Color palette":
            self.violin_color_scheme_msg.SetLabel("You can change the color palette in the 'General' tab.")
        else:
            self.violin_color_scheme_msg.SetLabel("")
        CONFIG.violin_colormap = self.violin_colormap_value.GetStringSelection()
        CONFIG.violin_normalize = self.violin_normalize_check.GetValue()
        CONFIG.violin_line_sameAsShade = self.violin_line_same_as_fill_check.GetValue()
        CONFIG.violin_shade_under_transparency = self.violin_fill_transparency_value.GetValue()
        CONFIG.violin_nlimit = self.violin_n_limit_value.GetValue()
        CONFIG.violin_label_format = self.violin_label_format_value.GetStringSelection()
        CONFIG.violin_labels_frequency = self.violin_label_frequency_value.GetValue()

        if evt is not None:
            evt.Skip()

    def on_apply_waterfall(self, evt):
        """Apply waterfall settings"""
        CONFIG.waterfall_offset = str2num(self.waterfall_offset_value.GetValue())
        CONFIG.waterfall_increment = self.waterfall_increment_value.GetValue()
        CONFIG.waterfall_lineWidth = self.waterfall_line_width_value.GetValue()
        CONFIG.waterfall_lineStyle = self.waterfall_line_style_value.GetStringSelection()
        CONFIG.waterfall_reverse = self.waterfall_reverse_check.GetValue()
        CONFIG.waterfall_color_value = self.waterfall_colorScheme_value.GetStringSelection()
        if CONFIG.waterfall_color_value == "Color palette":
            self.waterfall_colorScheme_msg.SetLabel("You can change the color palette in the 'General' tab.")
        else:
            self.waterfall_colorScheme_msg.SetLabel("")
        CONFIG.waterfall_colormap = self.waterfall_colormap_value.GetStringSelection()
        CONFIG.waterfall_normalize = self.waterfall_normalize_check.GetValue()
        CONFIG.waterfall_line_sameAsShade = self.waterfall_line_sameAsShade_check.GetValue()
        CONFIG.waterfall_add_labels = self.waterfall_showLabels_check.GetValue()
        CONFIG.waterfall_labels_frequency = self.waterfall_label_frequency_value.GetValue()
        CONFIG.waterfall_labels_x_offset = self.waterfall_label_x_offset_value.GetValue()
        CONFIG.waterfall_labels_y_offset = self.waterfall_label_y_offset_value.GetValue()
        CONFIG.waterfall_label_fontSize = self.waterfall_label_font_size_value.GetValue()
        CONFIG.waterfall_label_fontWeight = self.waterfall_label_font_weight_check.GetValue()
        CONFIG.waterfall_shade_under = self.waterfall_fill_under_check.GetValue()
        CONFIG.waterfall_shade_under_transparency = self.waterfall_fill_transparency_value.GetValue()
        CONFIG.waterfall_shade_under_nlimit = self.waterfall_fill_n_limit_value.GetValue()
        CONFIG.waterfall_label_format = self.waterfall_label_format_value.GetStringSelection()

        if evt is not None:
            evt.Skip()

    def on_apply_rmsd(self, evt):
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

    def on_assign_color(self, evt):
        """Update colors"""
        if self.import_evt:
            return

        evt_id = evt.GetId()

        dlg = DialogColorPicker(self, CONFIG.customColors)
        if dlg.ShowModal() != wx.ID_OK:
            return
        color_255, color_1, __ = dlg.GetChosenColour()
        CONFIG.customColors = dlg.GetCustomColours()

        if evt_id == ID_extraSettings_labelColor_rmsd:
            CONFIG.rmsd_color = color_1
            self.rmsd_color_btn.SetBackgroundColour(color_255)
            self.on_update_rmsd_label(None)

        elif evt_id == ID_extraSettings_lineColor_rmsd:
            CONFIG.rmsd_lineColour = color_1
            self.rmsd_color_line_btn.SetBackgroundColour(color_255)
            self.panel_plot.plot_1D_update(plotName="RMSF")

        elif evt_id == ID_extraSettings_underlineColor_rmsd:
            CONFIG.rmsd_underlineColor = color_1
            self.rmsd_underline_color_btn.SetBackgroundColour(color_255)
            self.panel_plot.plot_1D_update(plotName="RMSF")

        elif evt_id == ID_extraSettings_markerColor_1D:
            CONFIG.markerColor_1D = color_1
            self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

        elif evt_id == ID_extraSettings_edgeMarkerColor_1D:
            CONFIG.markerEdgeColor_1D = color_1
            self.plot1d_marker_edge_color_btn.SetBackgroundColour(color_255)

        elif evt_id == ID_extraSettings_lineColor_1D:
            CONFIG.lineColour_1D = color_1
            self.plot1d_line_color_btn.SetBackgroundColour(color_255)
            self.on_update_1d(None)

        elif evt_id == ID_extraSettings_shadeUnderColor_1D:
            CONFIG.lineShadeUnderColour_1D = color_1
            self.plot1d_underline_color_btn.SetBackgroundColour(color_255)
            self.on_update_1d(None)

        elif evt_id == ID_extraSettings_boxColor:
            CONFIG._plots_zoom_box_color = color_1
            self.zoom_zoom_box_color_btn.SetBackgroundColour(color_255)

        elif evt_id == ID_extraSettings_verticalColor:
            CONFIG._plots_zoom_vertical_color = color_1
            self.zoom_zoom_vertical_color_btn.SetBackgroundColour(color_255)

        elif evt_id == ID_extraSettings_horizontalColor:
            CONFIG._plots_zoom_horizontal_color = color_1
            self.zoom_zoom_horizontal_color_btn.SetBackgroundColour(color_255)

        elif evt_id == ID_extraSettings_lineColour_waterfall:
            CONFIG.waterfall_color = color_1
            self.waterfall_color_line_btn.SetBackgroundColour(color_255)
            self.on_update_2d(evt)

        elif evt_id == ID_extraSettings_shadeColour_waterfall:
            CONFIG.waterfall_shade_under_color = color_1
            self.waterfall_color_fill_btn.SetBackgroundColour(color_255)
            self.on_update_2d(evt)

        elif evt_id == ID_extraSettings_lineColour_violin:
            CONFIG.violin_color = color_1
            self.violin_color_line_btn.SetBackgroundColour(color_255)
            self.on_update_2d(evt)

        elif evt_id == ID_extraSettings_shadeColour_violin:
            CONFIG.violin_shade_under_color = color_1
            self.violin_color_fill_btn.SetBackgroundColour(color_255)
            self.on_update_2d(evt)

        elif evt_id == ID_extraSettings_bar_edgeColor:
            CONFIG.bar_edge_color = color_1
            self.bar_edge_color_btn.SetBackgroundColour(color_255)
        else:
            obj_name = evt.GetEventObject().GetName()
            if obj_name == "colorbar.outline":
                CONFIG.colorbar_edge_color = color_1
                self.colorbar_outline_color_btn.SetBackgroundColour(color_255)
                self.on_update_2d(evt)
            elif obj_name == "colorbar.label":
                CONFIG.colorbar_label_color = color_1
                self.colorbar_label_color_btn.SetBackgroundColour(color_255)
                self.on_update_2d(evt)
            elif obj_name == "rmsd_matrix_label":
                CONFIG.rmsd_matrix_font_color = color_1
                self.rmsd_matrix_font_color_btn.SetBackgroundColour(color_255)
                self.on_update_2d(evt)

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

        if evt is not None:
            evt.Skip()

    def on_update_rmsd_label(self, evt):
        """Update RMSD label"""
        self.on_apply_rmsd(None)
        self._recalculate_rmsd_position(None)

        self.panel_plot.plot_2D_update_label()

        if evt is not None:
            evt.Skip()

    def on_update_label_rmsd_matrix(self, evt):
        """Update RMSD matrix labels"""
        self.on_apply_rmsd(None)

        self.panel_plot.plot_2D_matrix_update_label()

        if evt is not None:
            evt.Skip()

    def on_update(self, evt):
        """General plot update"""
        print(self)
        # t_start = time.time()
        # self.on_apply_1d(None)
        #
        # if self.panel_plot.currentPage in ["Mass spectrum", "Chromatogram", "Mobilogram"]:
        #     if self.panel_plot.window_plot1D == "Mass spectrum":
        #         self.panel_plot.plot_1D_update(plotName="MS")
        #
        #     elif self.panel_plot.window_plot1D == "Chromatogram":
        #         self.panel_plot.plot_1D_update(plotName="RT")
        #
        #     elif self.panel_plot.window_plot1D == "Mobilogram":
        #         self.panel_plot.plot_1D_update(plotName="1D")
        #
        # if self.panel_plot.currentPage in ["Heatmap", "DT/MS", "Waterfall"]:
        #     if self.panel_plot.window_plot2D == "Heatmap":
        #         self.panel_plot.plot_2D_update(plotName="2D")
        #
        #     elif self.panel_plot.window_plot2D == "DT/MS":
        #         self.panel_plot.plot_2D_update(plotName="DT/MS")
        #
        #     elif self.panel_plot.window_plot2D == "Waterfall":
        #         try:
        #             source = evt.GetEventObject().GetName()
        #         except Exception:
        #             source = "axes"
        #         self.panel_plot.plot_1D_waterfall_update(source)
        #
        # if self.panel_plot.currentPage == "Annotated":
        #     plot_name = self.panel_plot.plotOther.plot_name
        #
        #     try:
        #         source = evt.GetEventObject().GetName()
        #     except AttributeError:
        #         source = "axes"
        #
        #     if plot_name == "waterfall":
        #         self.panel_plot.plot_1D_waterfall_update(source)
        #     elif plot_name == "2D":
        #         self.panel_plot.plot_2D_update(plotName="other")
        #     elif plot_name in ["RMSF", "RMSD"]:
        #         self.panel_plot.plot_1D_update(plotName="RMSF")
        #     else:
        #         self.panel_plot.plot_1D_update(plotName=plot_name)
        #
        # if self.panel_plot.window_plot3D == "Heatmap (3D)":
        #     self.panel_plot.plot_3D_update(plotName="3D")
        #
        # logger.debug(f"update {source} / plot_name {plot_name} in {time.time()-t_start:.4f}s")
        if evt is not None:
            evt.Skip()

    def on_update_1d(self, evt):
        """Update 1d plots"""
        print(self)
        # self.on_apply_1d(None)
        # if self.panel_plot.window_plot1D == "Mass spectrum":
        #     self.panel_plot.plot_1D_update(plotName="MS")
        #
        # elif self.panel_plot.window_plot1D == "Chromatogram":
        #     self.panel_plot.plot_1D_update(plotName="RT")
        #
        # elif self.panel_plot.window_plot1D == "Mobilogram":
        #     self.panel_plot.plot_1D_update(plotName="1D")

        if evt is not None:
            evt.Skip()

    def on_update_2d(self, evt):
        """Update 2d plots"""
        print(self)
        # t_start = time.time()
        #
        # # update config values
        # self.on_apply_1d(None)
        # self.on_apply_2d(None)

        #
        #         source = evt.GetEventObject().GetName()
        #
        #         # Heatmap-like
        #         if self.panel_plot.window_plot2D in ["Heatmap", "DT/MS", "Annotated"]:
        #             if source == "colorbar" or "colorbar" in source:
        #                 self.panel_plot.plot_colorbar_update(self.panel_plot.window_plot2D)
        #             elif source == "normalization":
        #                 self.panel_plot.plot_normalization_update(self.panel_plot.window_plot2D)
        #             elif source == "rmsf":
        #                 self.panel_plot.plot_1D_update(plotName="RMSF")
        #             elif source in ["rmsf.spacing", "rmsd_matrix_formatter"]:
        #                 logger.warning("Quick update not implemented yet - you will have to fully replot the plot")
        #             elif source in ["rmsd_matrix", "rmsd_matrix_label"]:
        #                 self.panel_plot.plot_2D_matrix_update_label()
        #             else:
        #                 self.panel_plot.plot_2D_update(plotName="2D")
        #         elif self.panel_plot.window_plot2D == "Waterfall" or self.panel_plot.currentPage == "Annotated":
        #
        #             if source in ["label.frequency"]:
        #                 logger.warning("Quick update not implemented yet - you will have to fully replot the plot")
        #             else:
        #                 self.panel_plot.plot_1D_waterfall_update(source)
        #
        #         logger.debug(f"update {source} in {time.time()-t_start:.4f}s")
        if evt is not None:
            evt.Skip()

    def on_update_3d(self, evt):
        """Update 3d plots"""
        print(self)
        # self.on_apply_3d(None)
        # if self.panel_plot.window_plot3D == "Heatmap (3D)":
        #     self.panel_plot.plot_3D_update(plotName="3D")

        if evt is not None:
            evt.Skip()

    def on_replot_1d(self, evt):
        """Full replot of the line plot"""
        print(self)
        # self.on_apply_1d(None)
        # if self.panel_plot.window_plot1D == "Mass spectrum":
        #     self.panel_plot.on_plot_ms(replot=True)
        #
        # elif self.panel_plot.window_plot1D == "Chromatogram":
        #     self.panel_plot.on_plot_rt(replot=True)
        #
        # elif self.panel_plot.window_plot1D == "Mobilogram":
        #     self.panel_plot.on_plot_1d(replot=True)

        if evt is not None:
            evt.Skip()

    def on_replot_2d(self, evt):
        """Full replot of heatmap"""
        print(self)
        # self.on_apply_2d(None)
        # if self.panel_plot.window_plot2D == "Heatmap":
        #     self.panel_plot.on_plot_2d(replot=True, full_repaint=True)
        #
        # elif self.panel_plot.window_plot2D == "DT/MS":
        #     self.panel_plot.on_plot_dtms(replot=True)
        #
        #         elif self.panel_plot.window_plot2D == "Comparison":
        #             self.panel_plot.on_plot_matrix(replot=True)

        if evt is not None:
            evt.Skip()

    def on_replot_3d(self, evt):
        """Full replot of 3d heatmap"""
        print(self)

        # self.on_apply_3d(None)
        # if self.panel_plot.window_plot3D == "Heatmap (3D)":
        #     self.panel_plot.on_plot_3D(replot=True)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_general(self, evt):
        """Update general controls"""
        self.plot_right_spines_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_top_spines_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_left_spines_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_bottom_spines_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_left_ticks_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_right_ticks_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_top_ticks_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_bottom_ticks_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_left_tick_labels_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_right_tick_labels_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_top_tick_labels_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_bottom_tick_labels_check.Enable(not CONFIG.axisOnOff_1D)
        self.plot_frame_width_value.Enable(not CONFIG.axisOnOff_1D)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_1d(self, evt):
        """Update line controls"""
        self.plot1d_marker_edge_color_btn.Enable(self.plot1d_marker_edge_color_check.GetValue())
        self.plot1d_marker_edge_color_btn.SetBackgroundColour(self.plot1d_marker_color_btn.GetBackgroundColour())

        self.plot1d_underline_color_btn.Enable(self.plot1d_underline_check.GetValue())
        self.plot1d_underline_alpha_value.Enable(self.plot1d_underline_check.GetValue())

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_2d(self, evt):
        """Update heatmap controls"""
        CONFIG.normalization_2D = self.plot2d_normalization_value.GetStringSelection()
        if CONFIG.normalization_2D == "Midpoint":
            self.plot2d_mid_value.Enable(True)
            self.plot2d_normalization_gamma_value.Enable(False)
        else:
            if CONFIG.normalization_2D == "Power":
                self.plot2d_normalization_gamma_value.Enable(True)
            else:
                self.plot2d_normalization_gamma_value.Enable(False)
            self.plot2d_mid_value.Enable(False)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_colorbar(self, evt):
        """Update colorbar controls"""
        CONFIG.colorbar = self.colorbar_tgl.GetValue()
        self.colorbar_tgl.SetLabel("On" if CONFIG.colorbar else "Off")
        self.colorbar_tgl.SetForegroundColour(wx.WHITE)
        self.colorbar_tgl.SetBackgroundColour(wx.BLUE if CONFIG.colorbar else wx.RED)

        self.colorbar_position_value.Enable(CONFIG.colorbar)
        self.colorbar_width_value.Enable(CONFIG.colorbar)
        self.colorbar_pad_value.Enable(CONFIG.colorbar)
        self.colorbar_fontsize_value.Enable(CONFIG.colorbar)
        self.colorbar_label_format.Enable(CONFIG.colorbar)
        self.colorbar_outline_width_value.Enable(CONFIG.colorbar)
        self.colorbar_label_color_btn.Enable(CONFIG.colorbar)
        self.colorbar_outline_color_btn.Enable(CONFIG.colorbar)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_legend(self, evt):
        """Update legend controls"""
        CONFIG.legend = self.legend_toggle.GetValue()
        self.legend_toggle.SetLabel("On" if CONFIG.legend else "Off")
        self.legend_toggle.SetForegroundColour(wx.WHITE)
        self.legend_toggle.SetBackgroundColour(wx.BLUE if CONFIG.legend else wx.RED)

        self.legend_position_value.Enable(CONFIG.legend)
        self.legend_columns_value.Enable(CONFIG.legend)
        self.legend_fontsize_value.Enable(CONFIG.legend)
        self.legend_frame_check.Enable(CONFIG.legend)
        self.legend_alpha_value.Enable(CONFIG.legend)
        self.legend_marker_size_value.Enable(CONFIG.legend)
        self.legend_n_markers_value.Enable(CONFIG.legend)
        self.legend_marker_before_check.Enable(CONFIG.legend)
        self.legend_fancybox_check.Enable(CONFIG.legend)
        self.legend_patch_alpha_value.Enable(CONFIG.legend)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_violin(self, evt):
        """Update violin controls"""
        CONFIG.violin_line_sameAsShade = self.violin_line_same_as_fill_check.GetValue()
        self.violin_color_line_btn.Enable(not CONFIG.violin_line_sameAsShade)

        CONFIG.violin_color_value = self.violin_colorScheme_value.GetStringSelection()
        if CONFIG.violin_color_value == "Same color":
            self.violin_colormap_value.Disable()
            self.violin_color_fill_btn.Enable()
        elif CONFIG.violin_color_value == "Colormap":
            self.violin_colormap_value.Enable()
            self.violin_color_fill_btn.Disable()
        else:
            self.violin_colormap_value.Disable()
            self.violin_color_fill_btn.Disable()

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_waterfall(self, evt):
        """Update waterfall controls"""
        CONFIG.waterfall_line_sameAsShade = self.waterfall_line_sameAsShade_check.GetValue()
        self.waterfall_color_line_btn.Enable(not CONFIG.waterfall_line_sameAsShade)

        # update patch coloring
        CONFIG.waterfall_shade_under = self.waterfall_fill_under_check.GetValue()
        self.waterfall_fill_transparency_value.Enable(CONFIG.waterfall_shade_under)
        self.waterfall_fill_n_limit_value.Enable(CONFIG.waterfall_shade_under)

        # update labels
        CONFIG.waterfall_add_labels = self.waterfall_showLabels_check.GetValue()
        self.waterfall_label_format_value.Enable(CONFIG.waterfall_add_labels)
        self.waterfall_label_font_size_value.Enable(CONFIG.waterfall_add_labels)
        self.waterfall_label_font_weight_check.Enable(CONFIG.waterfall_add_labels)
        self.waterfall_label_frequency_value.Enable(CONFIG.waterfall_add_labels)
        self.waterfall_label_x_offset_value.Enable(CONFIG.waterfall_add_labels)
        self.waterfall_label_y_offset_value.Enable(CONFIG.waterfall_add_labels)

        CONFIG.waterfall_color_value = self.waterfall_colorScheme_value.GetStringSelection()
        if CONFIG.waterfall_color_value == "Same color" and CONFIG.waterfall:
            self.waterfall_colormap_value.Disable()
        elif CONFIG.waterfall_color_value == "Colormap" and CONFIG.waterfall:
            self.waterfall_colormap_value.Enable()
        else:
            self.waterfall_colormap_value.Disable()

        if evt is not None:
            evt.Skip()

    def on_toggle_controls_rmsd(self, evt):
        """Update RMSD settings"""

        CONFIG.rmsd_position = self.rmsd_position_value.GetStringSelection()
        self.rmsd_x_position_value.Enable(CONFIG.rmsd_position == "other")
        self.rmsd_y_position_value.Enable(CONFIG.rmsd_position == "other")

        CONFIG.rmsd_matrix_font_color_choice = self.rmsd_matrix_color_fmt.GetStringSelection()
        self.rmsd_matrix_font_color_btn.Enable(CONFIG.rmsd_matrix_font_color_choice != "auto")

        if evt is not None:
            evt.Skip()

    def on_update_plot_sizes(self, evt):
        """Update plot sizes"""

        # get current plot name
        plot_name = self.general_plot_name_value.GetStringSelection()

        # get axes sizes
        plot_values = CONFIG._plotSettings[plot_name]  # noqa

        # update axes sizes
        axes_size = plot_values["axes_size"]
        for i, item in enumerate(
            [self.general_left_value, self.general_bottom_value, self.general_width_value, self.general_height_value]
        ):
            item.SetValue(axes_size[i])

        # update plot sizes
        plot_sizes = plot_values["resize_size"]
        for i, item in enumerate([self.general_width_inch_value, self.general_height_inch_value]):
            item.SetValue(plot_sizes[i])

        if evt is not None:
            evt.Skip()

    def on_change_plot_style(self, evt):
        """Change plot sizes"""
        if self.import_evt:
            return

        CONFIG.currentStyle = self.plot_style_value.GetStringSelection()
        self.panel_plot.on_change_plot_style()

        if evt is not None:
            evt.Skip()

    def on_change_color_palette(self, evt):
        """Update color palette"""
        if self.import_evt:
            return

        CONFIG.currentPalette = self.plot_palette_value.GetStringSelection()
        self.panel_plot.on_change_color_palette(evt=None)

        if evt is not None:
            evt.Skip()

    def on_update_states(self, evt):
        """Update states"""
        if self.import_evt:
            return

        evt_id = evt.GetId()

        CONFIG.logging = self.general_log_to_file_check.GetValue()
        CONFIG.autoSaveSettings = self.general_auto_save_check.GetValue()

        if evt_id == ID_extraSettings_autoSaveSettings:
            on_off = "enabled" if CONFIG.autoSaveSettings else "disabled"
            msg = f"Auto-saving of settings was `{on_off}``"
        elif evt_id == ID_extraSettings_logging:
            on_off = "enabled" if CONFIG.logging else "disabled"
            msg = f"Logging to file was `{on_off}``"
        else:
            return

        logger.info(msg)
        if evt is not None:
            evt.Skip()


def _main():
    app = wx.App()

    ex = PanelVisualisationSettingsEditor(None, None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
