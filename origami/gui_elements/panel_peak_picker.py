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
logger = logging.getLogger("origami")


class panel_peak_picker(wx.MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
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
        self.CentreOnScreen()
        self.SetFocus()

        # setup kwargs
        self.document = kwargs.pop("document", None)
        self.document_title = kwargs.pop("document_title", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.mz_data = kwargs.pop("mz_data", None)

        # initilize plot
        self.on_plot_spectrum()

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        wx.EVT_SIZE(self, self.on_resize)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):

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

    def on_resize(self, evt):
        self.Layout()

    def make_settings_panel(self, split_panel):

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
                                            validator=validator('intPos'))
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

        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

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
        logger.info("Not implemented yet")

    def on_toggle_controls(self, evt):
        logger.info("Not implemented yet")

    def on_find_peaks(self, evt):
        print(self.document_title, self.dataset_name)
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]
        found_peaks = self.data_processing.find_peaks_in_mass_spectrum(
            mz_x=mz_x, mz_y=mz_y, return_data=True)
        print(found_peaks)

    def on_plot_spectrum(self):
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]

        self.panel_plot.on_plot_MS(mz_x, mz_y, show_in_window="peak_picker", plot_obj=self.plot_window)
