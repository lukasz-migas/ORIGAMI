# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import Dialog
from styles import makeCheckbox


class DialogAskOverride(Dialog):
    def __init__(self, parent, config, msg=None, **kwargs):
        Dialog.__init__(self, parent, title="Conflicting name...", **kwargs)

        self.parent = parent
        self.config = config
        self.make_gui()
        self.CentreOnParent()

        if msg is None:
            msg = "Item already exists in the document. What would you like to do?"
        self.msg.SetLabel(msg)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)

        self.msg = wx.StaticText(panel, -1, "", size=(400, 100))

        self.override_btn = wx.Button(panel, wx.ID_ANY, "Override", size=(-1, 22))
        self.override_btn.Bind(wx.EVT_BUTTON, self.override)

        self.merge_btn = wx.Button(panel, wx.ID_ANY, "Merge", size=(-1, 22))
        self.merge_btn.Bind(wx.EVT_BUTTON, self.merge)

        self.copy_btn = wx.Button(panel, wx.ID_OK, "Create copy", size=(-1, 22))
        self.copy_btn.Bind(wx.EVT_BUTTON, self.create_copy)

        self.not_ask_again_check = makeCheckbox(panel, "Don't ask again")
        self.not_ask_again_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.msg, (y, 0), wx.GBSpan(1, 4))
        y = y + 1
        grid.Add(self.override_btn, (y, 0), flag=wx.ALIGN_CENTER)
        grid.Add(self.merge_btn, (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.copy_btn, (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.not_ask_again_check, (y, 3), flag=wx.ALIGN_CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def override(self, evt):
        self.config.import_duplicate_action = "override"
        self.EndModal(wx.OK)

    def merge(self, evt):
        self.config.import_duplicate_action = "merge"
        self.EndModal(wx.OK)

    def create_copy(self, evt):
        self.config.import_duplicate_action = "duplicate"
        self.EndModal(wx.OK)

    def on_apply(self, evt):
        self.config.import_duplicate_ask = self.not_ask_again_check.GetValue()
