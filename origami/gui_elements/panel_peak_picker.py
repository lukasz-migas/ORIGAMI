# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
#      GitHub : https://github.com/lukasz-migas/ORIGAMI
#      University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#      Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas
import wx
import numpy as np

from visuals import mpl_plots
from styles import validator, makeCheckbox

import logging
from utils.converters import str2num, str2int
logger = logging.getLogger("origami")


# TODO: add control swap between Native and small-molecule peak picker
class panel_peak_picker(wx.MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        """Initlize panel"""
        wx.MiniFrame.__init__(self, parent, -1, 'Peak picker...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.view = parent
        self.presenter = presenter
        self.document_tree = self.view.panelDocuments.documents
        self.panel_plot = self.view.panelPlots

        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling

        self.displaysize = wx.GetDisplaySize()
        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0] - 320) / self.displayRes[0]

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
        self.on_plot_spectrum()

        # pre-allocae space
        self.recompute_peaks = True
        self.peaks_dict = None
        self.labels = None

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):
        """Make miniframe"""
        panel = wx.Panel(self, -1, size=(-1, -1))
        self.settings_panel = self.make_settings_panel(panel)
        self.plot_panel = self.make_plot_panel(panel)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.settings_panel, 1, wx.EXPAND)
        self.main_sizer.Add(self.plot_panel, 1, wx.EXPAND)
        self.main_sizer.Fit(panel)

        self.main_sizer.Fit(panel)
        self.SetSize((1100, 600))
        self.SetSizer(self.main_sizer)
        self.Layout()

    def make_settings_panel(self, split_panel):
        """Make settings panel"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1))

        mz_limit_check = wx.StaticText(panel, wx.ID_ANY, "Select mass range:")
        self.mz_limit_check = makeCheckbox(panel, "")
        self.mz_limit_check.SetValue(self.config.peak_find_mz_limit)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        mz_min_value = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.mz_min_value.SetValue(str(self.config.peak_find_mz_min))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_value = wx.StaticText(panel, wx.ID_ANY, "m/z end:")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.mz_max_value.SetValue(str(self.config.peak_find_mz_max))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        threshold_value = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                               validator=validator('floatPos'))
        self.threshold_value.SetValue(str(self.config.peak_find_threshold))
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        width_value = wx.StaticText(panel, wx.ID_ANY, "Minimal width:")
        self.width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.width_value.SetValue(str(self.config.peak_find_width))
        self.width_value.Bind(wx.EVT_TEXT, self.on_apply)

        relative_height_value = wx.StaticText(panel, wx.ID_ANY, "Relative height of peak width:")
        self.relative_height_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.relative_height_value.SetValue(str(self.config.peak_find_relative_height))
        self.relative_height_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_intensity_value = wx.StaticText(panel, wx.ID_ANY, "Minimal intensity:")
        self.min_intensity_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.min_intensity_value.SetValue(str(self.config.peak_find_min_intensity))
        self.min_intensity_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_distance_value = wx.StaticText(panel, wx.ID_ANY, "Minimal distance between peaks:")
        self.min_distance_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.min_distance_value.SetValue(str(self.config.peak_find_distance))
        self.min_distance_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_width_modifier_value = wx.StaticText(panel, wx.ID_ANY, "Peak width modifier:")
        self.peak_width_modifier_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.peak_width_modifier_value.SetValue(str(self.config.peak_find_peak_width_modifier))
        self.peak_width_modifier_value.Bind(wx.EVT_TEXT, self.on_apply)

        verbose_check = wx.StaticText(panel, wx.ID_ANY, "Verbose:")
        self.verbose_check = makeCheckbox(panel, "")
        self.verbose_check.SetValue(self.config.peak_find_verbose)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        visualize_highlight_check = wx.StaticText(panel, wx.ID_ANY, "Highlight:")
        self.visualize_highlight_check = makeCheckbox(panel, "")
        self.visualize_highlight_check.SetValue(self.config.fit_highlight)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        visualize_show_labels_check = wx.StaticText(panel, wx.ID_ANY, "Labels:")
        self.visualize_show_labels_check = makeCheckbox(panel, "")
        self.visualize_show_labels_check.SetValue(self.config.fit_show_labels)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        visualize_max_labels = wx.StaticText(panel, wx.ID_ANY, "Max no. labels:")
        self.visualize_max_labels = wx.SpinCtrlDouble(panel, -1,
                                                value=str(self.config.fit_show_labels_max_count),
                                                min=0, max=250,
                                                initial=self.config.fit_show_labels_max_count,
                                                inc=50, size=(90, -1))
        self.visualize_max_labels.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.visualize_show_labels_mz_check = makeCheckbox(panel, "m/z")
        self.visualize_show_labels_mz_check.SetValue(self.config.fit_show_labels_mz)
        self.visualize_show_labels_mz_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.visualize_show_labels_int_check = makeCheckbox(panel, "intensity")
        self.visualize_show_labels_int_check.SetValue(self.config.fit_show_labels_int)
        self.visualize_show_labels_int_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        data_add_peaks_to_peaklist = wx.StaticText(panel, wx.ID_ANY, "Add peaks to peak list:")
        self.data_add_peaks_to_peaklist = makeCheckbox(panel, "")
        self.data_add_peaks_to_peaklist.SetValue(self.config.fit_addPeaks)
        self.data_add_peaks_to_peaklist.Bind(wx.EVT_CHECKBOX, self.on_apply)

        data_add_peaks_to_annotations = wx.StaticText(panel, wx.ID_ANY, "Add peaks to annotations:")
        self.data_add_peaks_to_annotations = makeCheckbox(panel, "")
        self.data_add_peaks_to_annotations.SetValue(self.config.fit_addPeaksToAnnotations)
        self.data_add_peaks_to_annotations.Bind(wx.EVT_CHECKBOX, self.on_apply)

        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # visualize grid
        annot_grid = wx.GridBagSizer(5, 5)
        n = 0
        annot_grid.Add(visualize_highlight_check, (n, 0), wx.GBSpan(1, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.visualize_highlight_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(visualize_show_labels_check, (n, 0), wx.GBSpan(1, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.visualize_show_labels_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        annot_grid.Add(visualize_max_labels, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.visualize_max_labels, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_mz_check, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        annot_grid.Add(self.visualize_show_labels_int_check, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # data grid
        data_grid = wx.GridBagSizer(5, 5)
        n = 0
        data_grid.Add(data_add_peaks_to_peaklist, (n, 0), wx.GBSpan(1, 1),
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        data_grid.Add(self.data_add_peaks_to_peaklist, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        data_grid.Add(data_add_peaks_to_annotations, (n, 0), wx.GBSpan(1, 1),
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        data_grid.Add(self.data_add_peaks_to_annotations, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(mz_limit_check, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_limit_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_min_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_max_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(threshold_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(width_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(relative_height_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.relative_height_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_intensity_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_intensity_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_distance_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_distance_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(peak_width_modifier_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_width_modifier_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(verbose_check, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.verbose_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(annot_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(data_grid, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(self.find_peaks_btn, (n, 0), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.close_btn, (n, 1), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):
        """Make plot panel"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1))
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition,
                                   wx.DefaultSize, wx.TAB_TRAVERSAL)

        self.plot_window = mpl_plots.plots(self.plot_panel, figsize=(self.figsizeX, 2),
                                           config=self.config)

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
        self.config.peak_find_threshold = str2num(self.threshold_value.GetValue())
        self.config.peak_find_width = str2int(self.width_value.GetValue())
        self.config.peak_find_relative_height = str2num(self.relative_height_value.GetValue())
        self.config.peak_find_min_intensity = str2num(self.min_intensity_value.GetValue())
        self.config.peak_find_distance = str2int(self.min_distance_value.GetValue())
        self.config.peak_find_peak_width_modifier = str2num(self.peak_width_modifier_value.GetValue())

        self.config.peak_find_verbose = self.verbose_check.GetValue()
        self.config.peak_find_mz_limit = self.mz_limit_check.GetValue()
        self.config.peak_find_mz_min = str2num(self.mz_min_value.GetValue())
        self.config.peak_find_mz_max = str2num(self.mz_max_value.GetValue())

        self.config.fit_highlight = self.visualize_highlight_check.GetValue()
        self.config.fit_show_labels = self.visualize_show_labels_check.GetValue()
        self.config.fit_show_labels_max_count = str2int(self.visualize_max_labels.GetValue())
        self.config.fit_show_labels_mz = self.visualize_show_labels_mz_check.GetValue()
        self.config.fit_show_labels_int = self.visualize_show_labels_int_check.GetValue()

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
        item_list = [self.visualize_max_labels,
                     self.visualize_show_labels_int_check,
                     self.visualize_show_labels_mz_check]
        for item in item_list:
            item.Enable(enable=self.config.fit_show_labels)

    def on_find_peaks(self, evt):
        """Detect peaks in the spectrum"""
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]
        peaks_dict = self.data_processing.find_peaks_in_mass_spectrum(
            mz_x=mz_x, mz_y=mz_y, return_data=True)

#         self.peaks_dict = peaks_dict

        # plot found peaks
        self.on_annotate_spectrum(peaks_dict)

    def on_plot_spectrum(self):
        """Plot mass spectrum"""
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]

        self.panel_plot.on_plot_MS(mz_x, mz_y, show_in_window="peak_picker", plot_obj=self.plot_window)

    def on_generate_labels(self, mz_x, mz_y):

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

    def on_annotate_spectrum(self, peaks_dict):
        """Highlight peaks in the spectrum"""
        peaks_x_values = peaks_dict["peaks_x_values"]
        peaks_y_values = peaks_dict["peaks_y_values"]
        peaks_width = peaks_dict["peaks_width"]
        peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]
        n_peaks = len(peaks_width)

        # clean-up previous patches
        self.panel_plot.on_clear_patches(plot=None, plot_obj=self.plot_window)
        self.panel_plot.on_clear_labels(plot=None, plot_obj=self.plot_window)
        self.panel_plot.on_clear_markers(plot=None, plot_obj=self.plot_window)

        if n_peaks == 0:
            return

        n_peaks_max = 1000
        if n_peaks > n_peaks_max:
            logger.warning(
                f"Cannot plot {n_peaks} as it would be very slow! Will only plot {n_peaks_max} first peaks instead.")

        self.panel_plot.on_add_marker(peaks_x_values, peaks_y_values,
                                      color=self.config.markerColor_1D,
                                      marker=self.config.markerShape_1D,
                                      size=self.config.markerSize_1D,
                                      plot=None,
                                      plot_obj=self.plot_window,
                                      test_yvals=True,
                                      clear_first=False)

        if self.config.fit_highlight:
            for peak_id, (mz_x_minus, mz_width, mz_height) in enumerate(
                zip(peaks_x_minus_width, peaks_width, peaks_y_values)):
                if peak_id == n_peaks_max - 1:
                    break
                self.panel_plot.on_plot_patches(mz_x_minus, 0, mz_width, mz_height,
                                                color=self.config.markerColor_1D,
                                                alpha=self.config.markerTransparency_1D,
                                                repaint=False, plot=None, plot_obj=self.plot_window)

        if self.config.fit_show_labels:
            labels = self.on_generate_labels(peaks_x_values, peaks_y_values)
            for mz_position, mz_intensity, label in labels:
                self.presenter.view.panelPlots.on_plot_labels(xpos=mz_position,
                                                              yval=mz_intensity / self.plot_window.y_divider, label=label,
                                                              repaint=False,
                                                              plot=None, plot_obj=self.plot_window)

        # replot plot in case anything was added
        self.plot_window.repaint()
