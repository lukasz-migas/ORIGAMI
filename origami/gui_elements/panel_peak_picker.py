# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import wx
from styles import makeCheckbox
from styles import makeMenuItem
from styles import MiniFrame
from styles import validator
from utils.converters import str2int
from utils.converters import str2num
from utils.ranges import get_min_max
from utils.screen import calculate_window_size
from utils.time import ttime
from visuals import mpl_plots

logger = logging.getLogger("origami")

# TODO: Add peakutils picker
# TODO: Add statusbar/text window which will write output information
# TODO: Increase MS plot size
# TODO: Improve peak picker


class panel_peak_picker(MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        """Initlize panel"""
        MiniFrame.__init__(
            self, parent, title="Peak picker...", style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        )
        self.view = parent
        self.presenter = presenter
        self.document_tree = self.view.panelDocuments.documents
        self.panel_plot = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.7, 0.6])

        # pre-allocate parameters
        self.recompute_peaks = True
        self.peaks_dict = None
        self.labels = None
        self.show_smoothed_spectrum = True

        # initilize gui
        self.make_gui()
        self.on_toggle_controls(None)
        self.CentreOnScreen()
        self.SetFocus()

        # setup kwargs
        self.document = kwargs.pop("document", None)
        self.document_title = kwargs.pop("document_title", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.mz_data = kwargs.pop("mz_data", None)

        # initilize plot
        if self.mz_data is not None:
            self.on_plot_spectrum(self.mz_data["xvals"], self.mz_data["yvals"])
            self._mz_xrange = get_min_max(self.mz_data["xvals"])
            self._mz_yrange = get_min_max(self.mz_data["yvals"])

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):

        menu = wx.Menu()
        save_figure_menu_item = makeMenuItem(
            menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)

        menu_action_copy_to_clipboard = makeMenuItem(
            parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        #         clear_plot_menu_item = makeMenuItem(
        #             menu, id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
        #         )
        #         menu.AppendSeparator()
        #         menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        #         self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_update_method(self, evt):
        page = self.panel_book.GetPageText(self.panel_book.GetSelection())
        self.config.peak_find_method = "small_molecule" if page == "Small molecule" else "native"

    def make_gui(self):
        """Make miniframe"""
        panel = wx.Panel(self, -1, size=(-1, -1), name="main")

        self.panel_book = wx.Notebook(panel, wx.ID_ANY, style=wx.NB_NOPAGETHEME)
        self.panel_book.SetBackgroundColour((240, 240, 240))
        self.panel_book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_update_method)

        self.settings_native = self.make_settings_panel_native(self.panel_book)
        self.panel_book.AddPage(self.settings_native, "Native MS", False)

        self.settings_small = self.make_settings_panel_small_molecule(self.panel_book)
        self.panel_book.AddPage(self.settings_small, "Small molecule", False)

        self.settings_mass_range = self.make_mass_selection_panel(panel)
        self.settings_panel = self.make_settings_panel(panel)

        # pack settings panel
        self.settings_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_sizer.Add(self.panel_book, 1, wx.EXPAND, 0)
        self.settings_sizer.Add(self.settings_mass_range, 0, wx.EXPAND)
        self.settings_sizer.Add(self.settings_panel, 1, wx.EXPAND)
        self.settings_sizer.Fit(panel)

        self._settings_panel_size = self.settings_sizer.GetSize()

        self.plot_panel = self.make_plot_panel(panel)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.settings_sizer, 1, wx.EXPAND)
        self.main_sizer.Add(self.plot_panel, 1, wx.EXPAND)
        self.main_sizer.Fit(panel)

        self.SetSize(self._window_size)
        self.SetSizer(self.main_sizer)
        self.Layout()

    def make_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        self.visualize_highlight_check = makeCheckbox(panel, "Highlight with patch")
        self.visualize_highlight_check.SetValue(self.config.fit_highlight)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.visualize_show_labels_check = makeCheckbox(panel, "Show labels on plot")
        self.visualize_show_labels_check.SetValue(self.config.fit_show_labels)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        visualize_max_labels = wx.StaticText(panel, wx.ID_ANY, "Max no. labels:")
        self.visualize_max_labels = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.fit_show_labels_max_count),
            min=0,
            max=250,
            initial=self.config.fit_show_labels_max_count,
            inc=50,
            size=(90, -1),
        )
        self.visualize_max_labels.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.visualize_show_labels_mz_check = makeCheckbox(panel, "m/z")
        self.visualize_show_labels_mz_check.SetValue(self.config.fit_show_labels_mz)
        self.visualize_show_labels_mz_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.visualize_show_labels_int_check = makeCheckbox(panel, "intensity")
        self.visualize_show_labels_int_check.SetValue(self.config.fit_show_labels_int)
        self.visualize_show_labels_int_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.data_add_peaks_to_peaklist = makeCheckbox(panel, "Add peaks to peak list")
        self.data_add_peaks_to_peaklist.SetValue(self.config.fit_addPeaks)
        self.data_add_peaks_to_peaklist.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.data_add_peaks_to_annotations = makeCheckbox(panel, "Add peaks to spectrum annotations")
        self.data_add_peaks_to_annotations.SetValue(self.config.fit_addPeaksToAnnotations)
        self.data_add_peaks_to_annotations.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.verbose_check = makeCheckbox(panel, "verbose")
        self.verbose_check.SetValue(self.config.peak_find_verbose)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # visualize grid
        annot_grid = wx.GridBagSizer(5, 5)
        n = 0
        annot_grid.Add(self.visualize_highlight_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(self.visualize_show_labels_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(visualize_max_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.visualize_max_labels, (n, 1), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_mz_check, (n, 2), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_int_check, (n, 3), flag=wx.EXPAND)

        # data grid
        data_grid = wx.GridBagSizer(5, 5)
        n = 0
        data_grid.Add(self.data_add_peaks_to_peaklist, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        data_grid.Add(self.data_add_peaks_to_annotations, (n, 0), (1, 2), flag=wx.EXPAND)

        # data grid
        btn_grid = wx.GridBagSizer(5, 5)
        n = 0
        btn_grid.Add(self.find_peaks_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.close_btn, (n, 1), flag=wx.EXPAND)
        btn_grid.Add(self.verbose_check, (n, 2), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(annot_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(data_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_mass_selection_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="mass_selection")

        self.mz_limit_check = makeCheckbox(panel, "Specify peak picking mass range")
        self.mz_limit_check.SetValue(self.config.peak_find_mz_limit)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        mz_min_value = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_min_value.SetValue(str(self.config.peak_find_mz_min))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_value = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_max_value.SetValue(str(self.config.peak_find_mz_max))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(self.mz_limit_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_min_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), flag=wx.EXPAND)
        grid.Add(mz_max_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def make_settings_panel_small_molecule(self, split_panel):
        """Make settings panel for small molecule peak picking"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="small_molecules")

        threshold_value = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.threshold_value.SetValue(str(self.config.peak_find_threshold))
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        width_value = wx.StaticText(panel, wx.ID_ANY, "Minimal width:")
        self.width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.width_value.SetValue(str(self.config.peak_find_width))
        self.width_value.Bind(wx.EVT_TEXT, self.on_apply)

        relative_height_value = wx.StaticText(panel, wx.ID_ANY, "Measure peak width at relative height:")
        self.relative_height_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.relative_height_value.SetValue(str(self.config.peak_find_relative_height))
        self.relative_height_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_intensity_value = wx.StaticText(panel, wx.ID_ANY, "Minimal intensity:")
        self.min_intensity_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.min_intensity_value.SetValue(str(self.config.peak_find_min_intensity))
        self.min_intensity_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_distance_value = wx.StaticText(panel, wx.ID_ANY, "Minimal distance between peaks:")
        self.min_distance_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.min_distance_value.SetValue(str(self.config.peak_find_distance))
        self.min_distance_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_width_modifier_value = wx.StaticText(panel, wx.ID_ANY, "Peak width modifier:")
        self.peak_width_modifier_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.peak_width_modifier_value.SetValue(str(self.config.peak_find_peak_width_modifier))
        self.peak_width_modifier_value.Bind(wx.EVT_TEXT, self.on_apply)

        #         horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        #         horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        #         grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        #         n += 1
        grid.Add(threshold_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(relative_height_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.relative_height_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_intensity_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_intensity_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_distance_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_distance_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(peak_width_modifier_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_width_modifier_value, (n, 1), flag=wx.EXPAND)
        n += 1
        #         grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(grid, 0, wx.FIXED_MINSIZE, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_settings_panel_native(self, split_panel):
        """Make settings panel for native MS peak picking"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="native")

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.fit_threshold_value.SetValue(str(self.config.fit_threshold))
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.fit_window_value.SetValue(str(self.config.fit_window))
        self.fit_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        fit_relative_height = wx.StaticText(panel, wx.ID_ANY, "Measure peak width at relative height:")
        self.fit_relative_height = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.fit_relative_height.SetValue(str(self.config.fit_relative_height))
        self.fit_relative_height.Bind(wx.EVT_TEXT, self.on_apply)

        smooth_label = wx.StaticText(panel, wx.ID_ANY, "Smooth peaks:")
        self.fit_smooth_check = makeCheckbox(panel, "")
        self.fit_smooth_check.SetValue(self.config.fit_smoothPeaks)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:")
        self.fit_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.fit_sigma_value.SetValue(str(self.config.fit_smooth_sigma))
        self.fit_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        # fmt: off
        # self.fit_show_smoothed = makeCheckbox(panel, "Show")
        # self.fit_show_smoothed.SetValue(self.show_smoothed_spectrum)
        # self.fit_show_smoothed.Bind(wx.EVT_CHECKBOX, self.on_apply)
        #
        # fit_isotopic_check = wx.StaticText(panel, wx.ID_ANY, "Enable charge state prediction:")
        # self.fit_isotopic_check = makeCheckbox(panel, "")
        # self.fit_isotopic_check.SetValue(self.config.fit_highRes)
        # self.fit_isotopic_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        # self.fit_isotopic_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        #
        # fit_isotopic_threshold = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        # self.fit_isotopic_threshold = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        # self.fit_isotopic_threshold.SetValue(str(self.config.fit_highRes_threshold))
        # self.fit_isotopic_threshold.Bind(wx.EVT_TEXT, self.on_apply)
        #
        # fit_isotopic_window = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        # self.fit_isotopic_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        # self.fit_isotopic_window.SetValue(str(self.config.fit_highRes_window))
        # self.fit_isotopic_window.Bind(wx.EVT_TEXT, self.on_apply)
        #
        # fit_isotopic_width = wx.StaticText(panel, wx.ID_ANY, "Peak width:")
        # self.fit_isotopic_width = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        # self.fit_isotopic_width.SetValue(str(self.config.fit_highRes_width))
        # self.fit_isotopic_width.Bind(wx.EVT_TEXT, self.on_apply)
        #
        # fit_isotopic_show_envelope = wx.StaticText(panel, wx.ID_ANY, "Show isotopic envelope:")
        # self.fit_isotopic_show_envelope = makeCheckbox(panel, "")
        # self.fit_isotopic_show_envelope.SetValue(self.config.fit_highRes_isotopicFit)
        # self.fit_isotopic_show_envelope.Bind(wx.EVT_CHECKBOX, self.on_apply)
        # fmt: on

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        #         horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        #         horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        #         horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        #         grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        #         n += 1
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_window_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(fit_relative_height, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_relative_height, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(smooth_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_smooth_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(sigma_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_sigma_value, (n, 1), flag=wx.EXPAND)
        #         grid.Add(self.fit_show_smoothed, (n, 2),  flag=wx.EXPAND)
        #         n += 1
        #         grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        # fmt: off
        # n += 1
        # grid.Add(fit_isotopic_check, (n, 0),  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.fit_isotopic_check, (n, 1),  flag=wx.EXPAND)
        # n += 1
        # grid.Add(fit_isotopic_threshold, (n, 0),  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.fit_isotopic_threshold, (n, 1),  flag=wx.EXPAND)
        # n += 1
        # grid.Add(fit_isotopic_window, (n, 0),  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.fit_isotopic_window, (n, 1),  flag=wx.EXPAND)
        # n += 1
        # grid.Add(fit_isotopic_width, (n, 0),  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.fit_isotopic_width, (n, 1),  flag=wx.EXPAND)
        # n += 1
        # grid.Add(fit_isotopic_show_envelope, (n, 0),  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.fit_isotopic_show_envelope, (n, 1),  flag=wx.EXPAND)
        # n += 1
        # grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        # fmt: on

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):
        """Make plot panel"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="plot")
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_window = mpl_plots.plots(self.plot_panel, figsize=figsize, config=self.config)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Fit()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        # fit layout
        panel.SetSizer(main_sizer)
        main_sizer.Fit(panel)

        return panel

    def on_apply(self, evt):
        """Event driven configuration updates"""
        # Small-molecule peak finder
        self.config.peak_find_threshold = str2num(self.threshold_value.GetValue())
        self.config.peak_find_width = str2int(self.width_value.GetValue())
        self.config.peak_find_relative_height = str2num(self.relative_height_value.GetValue())
        self.config.peak_find_min_intensity = str2num(self.min_intensity_value.GetValue())
        self.config.peak_find_distance = str2int(self.min_distance_value.GetValue())

        self.config.peak_find_peak_width_modifier = str2num(self.peak_width_modifier_value.GetValue())
        self.config.fit_relative_height = str2num(self.fit_relative_height.GetValue())

        # Native-MS peak finder
        self.config.fit_threshold = str2num(self.fit_threshold_value.GetValue())
        self.config.fit_window = str2int(self.fit_window_value.GetValue())
        self.config.fit_smoothPeaks = self.fit_smooth_check.GetValue()
        self.config.fit_smooth_sigma = str2num(self.fit_sigma_value.GetValue())
        #         self.config.fit_highRes = self.fit_isotopic_check.GetValue()
        #         self.config.fit_highRes_threshold = str2num(self.fit_isotopic_threshold.GetValue())
        #         self.config.fit_highRes_window = str2int(self.fit_isotopic_window.GetValue())
        #         self.config.fit_highRes_width = str2num(self.fit_isotopic_width.GetValue())
        #         self.config.fit_highRes_isotopicFit = self.fit_isotopic_show_envelope.GetValue()

        # Mass range
        self.config.peak_find_mz_limit = self.mz_limit_check.GetValue()
        self.config.peak_find_mz_min = str2num(self.mz_min_value.GetValue())
        self.config.peak_find_mz_max = str2num(self.mz_max_value.GetValue())

        # visualisation
        self.config.peak_find_verbose = self.verbose_check.GetValue()
        self.config.fit_highlight = self.visualize_highlight_check.GetValue()
        self.config.fit_show_labels = self.visualize_show_labels_check.GetValue()
        self.config.fit_show_labels_max_count = str2int(self.visualize_max_labels.GetValue())
        self.config.fit_show_labels_mz = self.visualize_show_labels_mz_check.GetValue()
        self.config.fit_show_labels_int = self.visualize_show_labels_int_check.GetValue()

        # ui
        self.config.fit_addPeaks = self.data_add_peaks_to_peaklist.GetValue()
        self.config.fit_addPeaksToAnnotations = self.data_add_peaks_to_annotations.GetValue()
        # gui parameters
        #         self.show_smoothed_spectrum = self.fit_show_smoothed.GetValue()

        if evt is not None:
            evt.Skip()

    def on_toggle_controls(self, evt):
        """Event driven GUI updates"""
        # mass range controls
        self.config.peak_find_mz_limit = self.mz_limit_check.GetValue()
        item_list = [self.mz_min_value, self.mz_max_value]
        for item in item_list:
            item.Enable(enable=self.config.peak_find_mz_limit)

        # labels controls
        self.config.fit_show_labels = self.visualize_show_labels_check.GetValue()
        item_list = [
            self.visualize_max_labels,
            self.visualize_show_labels_int_check,
            self.visualize_show_labels_mz_check,
        ]
        for item in item_list:
            item.Enable(enable=self.config.fit_show_labels)

        #         # isotopic controls
        #         self.config.fit_highRes = self.fit_isotopic_check.GetValue()
        #         item_list = [self.fit_isotopic_show_envelope, self.fit_isotopic_threshold,
        #                      self.fit_isotopic_width, self.fit_isotopic_window]
        #         for item in item_list:
        #             item.Enable(enable=self.config.fit_highRes)

        # smooth MS
        self.config.fit_smoothPeaks = self.fit_smooth_check.GetValue()
        item_list = [
            self.fit_sigma_value,
            #                      self.fit_show_smoothed
        ]
        for item in item_list:
            item.Enable(enable=self.config.fit_smoothPeaks)

    def on_find_peaks(self, evt):
        """Detect peaks in the spectrum"""
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]

        if self.config.peak_find_method == "small_molecule":
            peaks_dict = self.data_processing.find_peaks_in_mass_spectrum_peak_properties(
                mz_x=mz_x, mz_y=mz_y, return_data=True
            )
        else:
            # pre-process
            if self.config.fit_smoothPeaks:
                mz_y = self.data_processing.smooth_spectrum(mz_y)
                self.on_plot_spectrum_update(mz_x, mz_y)

            peaks_dict = self.data_processing.find_peaks_in_mass_spectrum_local_max(
                mz_x=mz_x, mz_y=mz_y, return_data=True
            )

        # plot found peaks
        self.on_annotate_spectrum(peaks_dict)

        if self.config.fit_addPeaks:
            self.on_add_to_peaklist(peaks_dict)

        if self.config.fit_addPeaksToAnnotations:
            raise ValueError("Not implemented yet")

    def on_plot_spectrum(self, mz_x, mz_y):
        """Plot mass spectrum"""
        self.panel_plot.on_plot_MS(mz_x, mz_y, show_in_window="peak_picker", plot_obj=self.plot_window, override=False)

    def on_plot_spectrum_update(self, mz_x, mz_y):
        """Update plot data without changing anything else"""
        self.panel_plot.on_update_plot_1D(mz_x, mz_y, None, plot_obj=self.plot_window)

    def on_generate_labels(self, mz_x, mz_y):
        """Generate labels that will be added to the plot"""

        labels = []
        for peak_id, (mz_position, mz_height) in enumerate(zip(mz_x, mz_y)):
            if peak_id == self.config.fit_show_labels_max_count - 1:
                break
            label = f""
            if self.config.fit_show_labels_mz:
                label = f"{mz_position:.2f}"
            if self.config.fit_show_labels_int:
                if label != "":
                    label += f", {mz_height:.2f}"
                else:
                    label = f"{mz_height:.2f}"

            labels.append([mz_position, mz_height, label])

        return labels

    def on_show_threshold_line(self, evt):
        if self.config.peak_find_method == "small_molecule":
            threshold = self.config.peak_find_threshold
        else:
            threshold = str2num(self.fit_threshold_value.GetValue())

        if self._mz_yrange is not None and threshold not in [None, 0]:
            __, y_max = self._mz_yrange

            # if threshold is below 1, we assume that its meant to be a proportion
            if threshold <= 1:
                threshold = y_max * threshold

            self.panel_plot.on_add_horizontal_line(*self._mz_xrange, threshold, self.plot_window)

        if evt is not None:
            evt.Skip()

    def on_annotate_spectrum(self, peaks_dict):
        """Highlight peaks in the spectrum"""
        tstart = ttime()
        peaks_x_values = peaks_dict["peaks_x_values"]
        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_width = peaks_dict["peaks_x_width"]
        peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]
        n_peaks = len(peaks_width)

        # clean-up previous patches
        self.panel_plot.on_clear_patches(plot=None, plot_obj=self.plot_window)
        self.panel_plot.on_clear_labels(plot=None, plot_obj=self.plot_window)
        self.panel_plot.on_clear_markers(plot=None, plot_obj=self.plot_window)

        if n_peaks == 0:
            return
        logger.info(f"Found {n_peaks} peaks in the spectrum")
        n_peaks_max = 1000
        if n_peaks > n_peaks_max:
            logger.warning(
                f"Cannot plot {n_peaks} as it would be very slow! Will only plot {n_peaks_max} first peaks instead."
            )

        # add markers to the plot area
        self.panel_plot.on_add_marker(
            peaks_x_values,
            peaks_y_values,
            color=self.config.markerColor_1D,
            marker=self.config.markerShape_1D,
            size=self.config.markerSize_1D,
            plot=None,
            plot_obj=self.plot_window,
            test_yvals=False,
            clear_first=False,
            test_yvals_with_preset_divider=True,
        )

        # add `rectangle`-like patches to the plot area to highlight each ion
        if self.config.fit_highlight:
            for peak_id, (mz_x_minus, mz_width, mz_height) in enumerate(
                zip(peaks_x_minus_width, peaks_width, peaks_y_values)
            ):
                if peak_id == n_peaks_max - 1:
                    break
                self.panel_plot.on_plot_patches(
                    mz_x_minus,
                    0,
                    mz_width,
                    mz_height,
                    color=self.config.markerColor_1D,
                    alpha=self.config.markerTransparency_1D,
                    repaint=False,
                    plot=None,
                    plot_obj=self.plot_window,
                )

        # add labels to the plot
        if self.config.fit_show_labels:
            labels = self.on_generate_labels(peaks_x_values, peaks_y_values)
            for mz_position, mz_intensity, label in labels:
                self.presenter.view.panelPlots.on_plot_labels(
                    xpos=mz_position,
                    yval=mz_intensity / self.plot_window.y_divider,
                    label=label,
                    repaint=False,
                    plot=None,
                    plot_obj=self.plot_window,
                )

        # replot plot in case anything was added
        self.plot_window.repaint()

        if self.config.peak_find_verbose:
            logger.info(f"Plotted peaks in {ttime()-tstart:.4f} seconds.")

    def on_add_to_peaklist(self, peaks_dict):
        document_type = self.document.dataType
        allowed_document_types = ["Type: ORIGAMI", "Type: MANUAL", "Type: Infrared", "Type: MassLynx"]

        if document_type not in allowed_document_types:
            logger.error(
                f"Document type {document_type} does not permit addition of found peaks to the"
                + f" peaklist. Allowed document types include {allowed_document_types}."
            )
            return

        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]
        peaks_x_plus_width = peaks_dict["peaks_x_plus_width"]

        for __, (mz_x_minus, mz_x_plus, mz_height) in enumerate(
            zip(peaks_x_minus_width, peaks_x_plus_width, peaks_y_values)
        ):
            if not self.ionPanel.on_check_duplicate(f"{mz_x_minus}-{mz_x_plus}", self.document_title):
                add_dict = {
                    "mz_start": mz_x_minus,
                    "mz_end": mz_x_plus,
                    "charge": 1,
                    "mz_ymax": mz_height,
                    "alpha": self.config.overlay_defaultAlpha,
                    "mask": self.config.overlay_defaultMask,
                    "document": self.document_title,
                }
                self.ionPanel.on_add_to_table(add_dict)

    def on_clear_plot(self, evt):
        self.plot_window.clearPlot()

    def on_save_figure(self, evt):
        plot_title = f"{self.document_title}_{self.dataset_name}".replace(" ", "-").replace(":", "")
        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()
