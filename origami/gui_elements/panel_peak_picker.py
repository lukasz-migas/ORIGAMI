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
from utils.exceptions import MessageError
from utils.ranges import get_min_max
from utils.screen import calculate_window_size
from utils.time import ttime
from visuals import mpl_plots

logger = logging.getLogger("origami")

# TODO: Add peakutils picker
# TODO: Increase MS plot size
# TODO: Improve peak picker


class panel_peak_picker(MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        """Initlize panel"""
        MiniFrame.__init__(
            self, parent, title="Peak picker...", style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        )
        tstart = ttime()

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

        # pre-allocate parameters#
        self._recompute_peaks = True
        self._peaks_dict = None
        self._labels = None
        self._show_smoothed_spectrum = True
        self._mz_xrange = [None, None]
        self._mz_yrange = [None, None]
        self._n_peaks_max = 1000

        # initilize gui
        self.make_gui()
        self.on_toggle_controls(None)

        # setup kwargs
        self.document = kwargs.pop("document", None)
        self.document_title = kwargs.pop("document_title", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.mz_data = kwargs.pop("mz_data", None)

        # initilize plot
        if self.mz_data is not None:
            self.on_plot_spectrum(None)
            self._mz_xrange = get_min_max(self.mz_data["xvals"])
            self._mz_yrange = get_min_max(self.mz_data["yvals"])
            self._mz_bin_width = self.data_processing.get_mz_spacing(self.mz_data["xvals"])
            self.on_show_threshold_line(None)
            self.on_show_window_size_in_mz(None)

        # trigger UI events
        self.on_update_method(None)

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        logger.info(f"Startup of peak picker took {ttime()-tstart:.2f} seconds")

    def on_right_click(self, evt):
        # ensure that user clicked inside the plot area
        if hasattr(evt.EventObject, "figure"):

            menu = wx.Menu()
            save_figure_menu_item = makeMenuItem(
                menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
            )
            menu.AppendItem(save_figure_menu_item)

            menu_action_copy_to_clipboard = makeMenuItem(
                parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu_plot_clear_labels = menu.Append(wx.ID_ANY, "Clear annotations")

            self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
            self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
            self.Bind(wx.EVT_MENU, self.on_clear_from_plot, menu_plot_clear_labels)

            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()

    def on_update_method(self, evt):
        page = self.panel_book.GetPageText(self.panel_book.GetSelection())
        self.config.peak_find_method = "small_molecule" if page == "Small molecule" else "native"
        self.on_show_threshold_line(None)

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

        self.settings_panel = self.make_settings_panel(panel)

        # pack settings panel
        self.settings_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_sizer.Add(self.panel_book, 1, wx.EXPAND, 0)
        self.settings_sizer.Add(self.settings_panel, 1, wx.ALIGN_CENTER)
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
        self.CentreOnScreen()
        self.SetFocus()

    def on_action_tools(self, evt):

        menu = wx.Menu()

        menu_action_restore_original_plot = makeMenuItem(parent=menu, text="Restore orignal plot")
        menu_action_add_peaks_to_peaklist = makeMenuItem(parent=menu, text="Add peaks to peaklist panel")
        menu_action_add_peaks_to_annotations = makeMenuItem(parent=menu, text="Add peaks to spectrum annotations")

        menu.Append(menu_action_restore_original_plot)
        menu.AppendSeparator()
        menu.Append(menu_action_add_peaks_to_peaklist)
        menu.Append(menu_action_add_peaks_to_annotations)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_plot_spectrum, menu_action_restore_original_plot)
        self.Bind(wx.EVT_MENU, self.on_add_to_peaklist, menu_action_add_peaks_to_peaklist)
        self.Bind(wx.EVT_MENU, self.on_add_to_annotations, menu_action_add_peaks_to_annotations)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        self.mz_limit_check = makeCheckbox(panel, "Specify peak picking mass range")
        self.mz_limit_check.SetValue(self.config.peak_find_mz_limit)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        mz_min_value = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_min_value.SetValue(str(self._mz_xrange[0]))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_value = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_max_value.SetValue(str(self._mz_xrange[1]))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.visualize_highlight_check = makeCheckbox(panel, "Highlight with patch")
        self.visualize_highlight_check.SetValue(self.config.fit_highlight)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_patches)

        self.visualize_show_labels_check = makeCheckbox(panel, "Show labels on plot")
        self.visualize_show_labels_check.SetValue(self.config.fit_show_labels)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_labels)

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

        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)

        self.plot_peaks_btn = wx.Button(panel, wx.ID_OK, "Plot peaks", size=(-1, 22))
        self.plot_peaks_btn.Bind(wx.EVT_BUTTON, self.on_annotate_spectrum)

        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, 22))
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_tools)

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.verbose_check = makeCheckbox(panel, "verbose")
        self.verbose_check.SetValue(self.config.peak_find_verbose)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # visualize grid
        annot_grid = wx.GridBagSizer(5, 5)
        n = 0
        annot_grid.Add(self.mz_limit_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(mz_min_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.mz_min_value, (n, 1), flag=wx.EXPAND)
        annot_grid.Add(mz_max_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.mz_max_value, (n, 3), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(self.visualize_highlight_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(self.visualize_show_labels_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(visualize_max_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.visualize_max_labels, (n, 1), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_mz_check, (n, 2), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_int_check, (n, 3), flag=wx.EXPAND)

        # data grid
        btn_grid = wx.GridBagSizer(5, 5)
        n = 0
        btn_grid.Add(self.find_peaks_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.plot_peaks_btn, (n, 1), flag=wx.EXPAND)
        btn_grid.Add(self.action_btn, (n, 2), flag=wx.EXPAND)
        btn_grid.Add(self.close_btn, (n, 3), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(annot_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(self.verbose_check, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER | wx.EXPAND, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_settings_panel_small_molecule(self, split_panel):
        """Make settings panel for small molecule peak picking"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="small_molecules")

        threshold_value = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.threshold_value.SetValue(str(self.config.peak_find_threshold))
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

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

        method_choice = wx.StaticText(panel, -1, "Method:")
        self.method_choice = wx.ComboBox(
            panel,
            -1,
            choices=["Local search", "Differential search"],
            value="Local search",
            style=wx.CB_READONLY,
            size=(-1, -1),
        )
        self.method_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.fit_threshold_value.SetValue(str(self.config.fit_threshold))
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.fit_window_value.SetValue(str(self.config.fit_window))
        self.fit_window_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_window_value.Bind(wx.EVT_TEXT, self.on_show_window_size_in_mz)

        self.fit_window_mz_spacing = wx.StaticText(panel, wx.ID_ANY, "")

        fit_relative_height = wx.StaticText(panel, wx.ID_ANY, "Measure peak width at relative height:")
        self.fit_relative_height = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.fit_relative_height.SetValue(str(self.config.fit_relative_height))
        self.fit_relative_height.Bind(wx.EVT_TEXT, self.on_apply)

        smooth_label = wx.StaticText(panel, wx.ID_ANY, "Smooth spectrum using Gaussian filter:")
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
        # self.fit_show_smoothed.SetValue(self._show_smoothed_spectrum)
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

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(method_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.method_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_window_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.fit_window_mz_spacing, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
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

        if evt is not None:
            evt.Skip()

    def on_show_window_size_in_mz(self, evt):
        """Display m/z spacing in the UI"""
        if self.config.peak_find_method == "native":
            mz_bins = str2int(self.fit_window_value.GetValue(), 0) * self._mz_bin_width
            self.fit_window_mz_spacing.SetLabel(f"{mz_bins:.4f} Da")

        if evt is not None:
            evt.Skip()

    def on_show_threshold_line(self, evt):
        """Display a horizontal line indicating the minimal intensity that will be picked"""
        if self.config.peak_find_method == "small_molecule":
            threshold = str2num(self.threshold_value.GetValue())
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
        logger.info("Started peak picking...")

        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]

        if self.config.peak_find_method == "small_molecule":
            peaks_dict = self.data_processing.find_peaks_in_mass_spectrum_peak_properties(
                mz_x=mz_x, mz_y=mz_y, return_data=True
            )
        elif self.config.peak_find_method == "native":
            method = self.method_choice.GetStringSelection()
            # pre-process
            if self.config.fit_smoothPeaks:
                mz_y = self.data_processing.smooth_spectrum(mz_y)
                self.on_plot_spectrum_update(mz_x, mz_y)

            if method == "Differential search":
                peaks_dict = self.data_processing.find_peaks_in_mass_spectrum_peakutils(
                    mz_x=mz_x, mz_y=mz_y, return_data=True
                )
            else:
                peaks_dict = self.data_processing.find_peaks_in_mass_spectrum_local_max(
                    mz_x=mz_x, mz_y=mz_y, return_data=True
                )

        self._peaks_dict = peaks_dict

        # plot found peaks
        self.on_annotate_spectrum(None)

    def on_plot_spectrum(self, evt):
        """Plot mass spectrum"""
        self.panel_plot.on_plot_MS(
            self.mz_data["xvals"],
            self.mz_data["yvals"],
            show_in_window="peak_picker",
            plot_obj=self.plot_window,
            override=False,
        )

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

    def on_annotate_spectrum(self, evt):
        """Highlight peaks in the spectrum"""
        tstart = ttime()
        tstart_verbose = ttime()
        peaks_dict = self._peaks_dict
        if not peaks_dict:
            raise MessageError(
                "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
            )

        peaks_x_values = peaks_dict["peaks_x_values"]
        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_width = peaks_dict["peaks_x_width"]
        n_peaks = len(peaks_width)

        if n_peaks == 0:
            return
        logger.info(f"Found {n_peaks} peaks in the spectrum")
        self._n_peaks_max = 1000
        if n_peaks > self._n_peaks_max:
            logger.warning(
                f"Cannot plot {n_peaks} as it would be very slow! "
                + "Will only plot {self._n_peaks_max} first peaks instead."
            )

        # clean-up previous patches
        self.on_clear_from_plot(None)
        if self.config.peak_find_verbose:
            logger.info(f"Cleared previous items in {ttime()-tstart_verbose:.4f} seconds")
            tstart_verbose = ttime()

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
        if self.config.peak_find_verbose:
            logger.info(f"Plotted markers in {ttime()-tstart_verbose:.4f} seconds")
            tstart_verbose = ttime()

        # add `rectangle`-like patches to the plot area to highlight each ion
        if self.visualize_highlight_check.GetValue():
            self.on_annotate_spectrum_with_patches(None)

            if self.config.peak_find_verbose:
                logger.info(f"Plotted patches in {ttime()-tstart_verbose:.4f} seconds")
                tstart_verbose = ttime()

        # add labels to the plot
        if self.visualize_show_labels_check.GetValue():
            self.on_annotate_spectrum_with_labels(None)

            if self.config.peak_find_verbose:
                logger.info(f"Plotted labels in {ttime()-tstart:.4f} seconds")

        # replot plot in case anything was added
        self.plot_window.repaint()

        if self.config.peak_find_verbose:
            logger.info(f"Plotted peaks in {ttime()-tstart:.4f} seconds.")

    def on_annotate_spectrum_with_patches(self, evt):

        peaks_dict = self._peaks_dict
        if not peaks_dict:
            raise MessageError(
                "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
            )

        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_width = peaks_dict["peaks_x_width"]
        peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]

        # add `rectangle`-like patches to the plot area to highlight each ion
        if self.visualize_highlight_check.GetValue():
            for peak_id, (mz_x_minus, mz_width, mz_height) in enumerate(
                zip(peaks_x_minus_width, peaks_width, peaks_y_values)
            ):
                if peak_id == self._n_peaks_max - 1:
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
        else:
            self.plot_window.plot_remove_patches(False)

        # only replot if triggered by an actual event
        if evt is not None:
            self.plot_window.repaint()

    def on_annotate_spectrum_with_labels(self, evt):

        peaks_dict = self._peaks_dict
        if not peaks_dict:
            raise MessageError(
                "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
            )

        peaks_x_values = peaks_dict["peaks_x_values"]
        peaks_y_values = peaks_dict["peaks_y_values"]

        if self.visualize_show_labels_check.GetValue():
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
        else:
            self.plot_window.plot_remove_text_and_lines(False)
        self.on_show_threshold_line(None)

        # only replot if triggered by an actual event
        if evt is not None:
            self.plot_window.repaint()
            evt.Skip()

    def on_clear_from_plot(self, evt):
        # clean-up previous patches
        self.plot_window.plot_remove_text_and_lines(False)
        self.plot_window.plot_remove_patches(False)
        self.plot_window.plot_remove_markers(False)
        self.on_show_threshold_line(None)

    def on_add_to_annotations(self, evt):
        from utils.labels import sanitize_string
        from objects.annotations import check_annotation_input

        tstart = ttime()
        logger.info("Adding peaks to annotations...")

        peaks_dict = self._peaks_dict
        if not peaks_dict:
            raise MessageError(
                "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
            )

        # get annotations object
        annotations_obj = self.data_handling.get_annotations_data(
            [self.document_title, self.dataset_name, self.dataset_name]
        )

        ymin = 0
        charge = 1
        for i, __ in enumerate(peaks_dict["peaks_y_values"]):
            # generate all required fields
            position = peaks_dict["peaks_x_values"][i]
            intensity = peaks_dict["peaks_y_values"][i]
            xmin = peaks_dict["peaks_x_minus_width"][i]
            xmax = peaks_dict["peaks_x_plus_width"][i]
            height = intensity - ymin
            width = xmax - xmin

            name = f"x={position:.4f}; y={intensity:.2f}"
            label = f"x={position:.4f}\ny={intensity:.2f}\ncharge={charge:d}"

            annotation_dict = {
                "name": name,
                "position_x": position,
                "position_y": intensity,
                "label": label,
                "label_position_x": position,
                "label_position_y": intensity,
                "label_position": [position, intensity],
                "arrow": True,
                "width": width,
                "height": height,
                "charge": charge,
                "patch_color": self.config.interactive_ms_annotations_color,
                "label_color": (0.0, 0.0, 0.0),
                "patch_position": [xmin, ymin, width, height],
                "patch": False,
            }
            name = sanitize_string(name)
            try:
                annotation_dict = check_annotation_input(annotation_dict)
            except ValueError as err:
                logger.error(err, exc_info=True)
                raise MessageError("Incorrect input", str(err))

            if name in annotations_obj:
                annotations_obj.update_annotation(name, annotation_dict)
            else:
                annotations_obj.add_annotation(name, annotation_dict)

        self.document_tree.on_update_annotation(
            annotations_obj, self.document_title, self.dataset_name, self.dataset_name
        )

        if self.config.peak_find_verbose:
            logger.info(f"Adding peaks to annotations object took {ttime()-tstart:.4f} seconds.")

    def on_add_to_peaklist(self, evt):
        tstart = ttime()
        logger.info("Adding peaks to peaklist...")

        peaks_dict = self._peaks_dict
        if not peaks_dict:
            raise MessageError(
                "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
            )

        document_type = self.document.dataType
        allowed_document_types = ["Type: ORIGAMI", "Type: MANUAL", "Type: Infrared", "Type: MassLynx"]

        if document_type not in allowed_document_types:
            raise MessageError(
                "Incorrect document type",
                f"Document type `{document_type}` does not permit addition of found peaks to the"
                + f" peaklist. Allowed document types include {allowed_document_types}.",
            )

        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]
        peaks_x_plus_width = peaks_dict["peaks_x_plus_width"]

        for __, (mz_x_minus, mz_x_plus, mz_height) in enumerate(
            zip(peaks_x_minus_width, peaks_x_plus_width, peaks_y_values)
        ):
            ion_name = f"{mz_x_minus:.4f}-{mz_x_plus:.4f}"
            if not self.ionPanel.on_check_duplicate(ion_name, self.document_title):
                add_dict = {
                    "ion_name": ion_name,
                    "charge": 1,
                    "mz_ymax": mz_height,
                    "alpha": self.config.overlay_defaultAlpha,
                    "mask": self.config.overlay_defaultMask,
                    "document": self.document_title,
                }
                self.ionPanel.on_add_to_table(add_dict)

        if self.config.peak_find_verbose:
            logger.info(f"Adding peaks to peaklist took {ttime()-tstart:.4f} seconds.")

    def on_clear_plot(self, evt):
        self.plot_window.clearPlot()

    def on_save_figure(self, evt):
        plot_title = f"{self.document_title}_{self.dataset_name}".replace(" ", "-").replace(":", "")
        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()
