# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
#     GitHub : https://github.com/lukasz-migas/ORIGAMI
#     University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#     Cite : 10.1016/j.ijms.2017.08.014
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
from styles import makeCheckbox, Dialog


class DialogMessagePopup(Dialog):

    def __init__(self, parent, title, msg, **kwargs):
        Dialog.__init__(self, parent, title='Warning', **kwargs)

        self.make_gui()
        self.CentreOnParent()

        self.msg.SetValue(msg)
        self.SetTitle(title)

        self.ask_again = False

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)

        self.msg = wx.TextCtrl(panel, -1, "", size=(400, 40),
                               style=wx.TE_READONLY | wx.TE_WORDWRAP)

        self.yes_btn = wx.Button(panel, wx.ID_ANY, "Yes", size=(-1, 22))
        self.yes_btn.Bind(wx.EVT_BUTTON, self.ok_yes)

        self.no_btn = wx.Button(panel, wx.ID_ANY, "No", size=(-1, 22))
        self.no_btn.Bind(wx.EVT_BUTTON, self.on_no)

        self.ask_again_check = makeCheckbox(panel, "Don't ask again")
        self.ask_again_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.msg, (y, 0), wx.GBSpan(1, 4))
        y = y + 1
        grid.Add(self.yes_btn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.no_btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.ask_again_check, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def ok_yes(self, evt):
        self.EndModal(wx.OK)

    def merge(self, evt):
        self.EndModal(wx.ID_YES)

    def on_no(self, evt):
        self.EndModal(wx.ID_NO)

    def on_apply(self, evt):
        self.ask_again = self.ask_again_check.GetValue()

