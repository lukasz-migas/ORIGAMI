# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from ids import ID_saveAllDocuments
from styles import Dialog


class DialogNotifyOpenDocuments(Dialog):

    def __init__(self, parent, **kwargs):
        Dialog.__init__(self, parent, title='Documents are still open...!')

        self.parent = parent
        self.presenter = kwargs['presenter']
        self.message = kwargs['message']

        self.make_gui()
        self.CentreOnParent()

    def on_ok(self, evt):
        self.EndModal(wx.OK)

    def onSaveDocument(self, evt):
        self.presenter.on_save_all_documents(ID_saveAllDocuments)
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, '')
        self.input_label.SetLabel(self.message)

        self.save_all_btn = wx.Button(panel, ID_saveAllDocuments, 'Save all', size=(-1, 22))
        self.continue_btn = wx.Button(panel, wx.ID_OK, 'Continue', size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, 'Cancel', size=(-1, 22))

        # bind
        self.save_all_btn.Bind(wx.EVT_BUTTON, self.onSaveDocument, id=ID_saveAllDocuments)
        self.continue_btn.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close, id=wx.ID_CANCEL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.save_all_btn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.continue_btn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancel_btn, (2, 3), wx.GBSpan(1, 1))

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel
