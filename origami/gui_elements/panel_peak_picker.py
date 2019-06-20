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
from styles import validator


class panel_peak_picker(wx.MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons):
        wx.MiniFrame.__init__(self, parent, -1, 'Peak picker...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
                              wx.MAXIMIZE_BOX)
        self.view = parent
        self.presenter = presenter
        self.documentTree = self.view.panelDocuments.documents
        self.data_handling = presenter.data_handling
        self.config = config
        self.icons = icons

        self.displaysize = wx.GetDisplaySize()
        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0] - 320) / self.displayRes[0]

        self.make_gui()

        # setup gui pview
#         self.on_setup_gui()

        self.CentreOnScreen()
        self.SetFocus()

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        wx.EVT_SPLITTER_DCLICK(self, wx.ID_ANY, self._onSash)

    def _onSash(self, evt):
        evt.Veto()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):

        # splitter window
        self.split_panel = wx.SplitterWindow(self, wx.ID_ANY, wx.DefaultPosition,
                                             wx.DefaultSize,
                                             wx.TAB_TRAVERSAL | wx.SP_3DSASH | wx.SP_LIVE_UPDATE)

        # make panels
        left_panel_size = 400
        self.settings_panel = self.make_settings_panel(self.split_panel)
        self.settings_panel.SetSize((left_panel_size, -1))
        self.settings_panel.SetMinSize((left_panel_size, -1))
        self.settings_panel.SetMaxSize((left_panel_size, -1))

        right_panel_size = 680
        self.plot_panel = self.make_plot_panel(self.split_panel)
        self.plot_panel.SetSize((right_panel_size, -1))
        self.plot_panel.SetMinSize((right_panel_size, -1))
        self.plot_panel.SetMaxSize((right_panel_size, -1))

        self.split_panel.SplitVertically(self.settings_panel, self.plot_panel)
        self.split_panel.SetSashGravity(0.0)
        self.split_panel.SetSashSize(5)
        self.split_panel.SetSashPosition((400))

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.split_panel, 1, wx.EXPAND)

        # fit layout
        self.main_sizer.Fit(self.split_panel)
        self.SetSizer(self.main_sizer)
        self.SetSize((1100, 600))
        self.Centre()
        self.Layout()
        self.SetFocus()

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        mz_min_value = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.mz_min_value.SetValue(str(self.config.fit_window))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_value = wx.StaticText(panel, wx.ID_ANY, "m/z end:")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.mz_max_value.SetValue(str(self.config.fit_window))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        threshold_value = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                               validator=validator('floatPos'))
        self.threshold_value.SetValue(str(self.config.fit_threshold))
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        width_value = wx.StaticText(panel, wx.ID_ANY, "Minimal width:")
        self.width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.width_value.SetValue(str(self.config.fit_window))
        self.width_value.Bind(wx.EVT_TEXT, self.on_apply)

        relative_height_value = wx.StaticText(panel, wx.ID_ANY, "Relative height of peak width:")
        self.relative_height_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.relative_height_value.SetValue(str(self.config.fit_window))
        self.relative_height_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_intensity_value = wx.StaticText(panel, wx.ID_ANY, "Minimal intensity:")
        self.min_intensity_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.min_intensity_value.SetValue(str(self.config.fit_window))
        self.min_intensity_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_distance_value = wx.StaticText(panel, wx.ID_ANY, "Minimal distance between peaks:")
        self.min_distance_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.min_distance_value.SetValue(str(self.config.fit_window))
        self.min_distance_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_width_modifier_value = wx.StaticText(panel, wx.ID_ANY, "Peak width modifier:")
        self.peak_width_modifier_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('floatPos'))
        self.peak_width_modifier_value.SetValue(str(self.config.fit_window))
        self.peak_width_modifier_value.Bind(wx.EVT_TEXT, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
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

        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
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
        pass
