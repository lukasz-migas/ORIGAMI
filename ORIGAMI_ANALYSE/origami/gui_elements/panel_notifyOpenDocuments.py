import wx
from ids import ID_saveAllDocuments


class panelNotifyOpenDocuments(wx.Dialog):

    def __init__(self, parent, presenter, message, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Documents are still open...!', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)

        self.parent = parent
        self.presenter = presenter
        self.message = message

        self.makeGUI()
        self.CentreOnParent()

    def onClose(self, evt):
        """Destroy this frame."""
        self.EndModal(wx.ID_NO)
    # ----

    def onOK(self, evt):
        self.EndModal(wx.OK)

    def onSaveDocument(self, evt):
        self.presenter.on_save_all_documents(ID_saveAllDocuments)
        self.EndModal(wx.OK)

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.saveAllBtn.Bind(wx.EVT_BUTTON, self.onSaveDocument, id=ID_saveAllDocuments)
        self.continueBtn.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose, id=wx.ID_CANCEL)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, "")
        self.input_label.SetLabel(self.message)

        self.saveAllBtn = wx.Button(panel, ID_saveAllDocuments, "Save all", size=(-1, 22))
        self.continueBtn = wx.Button(panel, wx.ID_OK, "Continue", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.saveAllBtn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.continueBtn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 3), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

