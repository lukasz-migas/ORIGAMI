import wx
from ids import ID_addNewOverlayDoc


class panelSelectDocument(wx.Dialog):
    """
    Duplicate ions
    """

    def __init__(self, parent, presenter, keyList, allowNewDoc=True):
        wx.Dialog.__init__(self, parent, -1, 'Select document...', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = keyList
        self.allowNewDoc = allowNewDoc

        # make gui items
        self.makeGUI()
        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        # If pressed Close, return nothing of value
        self.presenter.currentDoc = None
        self.current_document = None

        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onSelectDocument, id=wx.ID_ANY)
        self.addBtn.Bind(wx.EVT_BUTTON, self.onNewDocument, id=ID_addNewOverlayDoc)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, "Choose document:")
        self.documentList_choice = wx.Choice(panel, -1, choices=self.documentList, size=(300, -1))
        self.documentList_choice.Select(0)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.addBtn = wx.Button(panel, ID_addNewOverlayDoc, "Add new document", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        # In some cases, we don't want to be able to create new document!
        if not self.allowNewDoc:
            self.addBtn.Disable()
        else:
            self.addBtn.Enable()

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(documentList_label, (0, 0))
        grid.Add(self.documentList_choice, (0, 1), wx.GBSpan(1, 3))

        grid.Add(self.okBtn, (1, 0), wx.GBSpan(1, 1))
        grid.Add(self.addBtn, (1, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (1, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onSelectDocument(self, evt):

        docName = self.documentList_choice.GetStringSelection()
        self.presenter.currentDoc = docName
        self.current_document = docName
        self.EndModal(wx.OK)

    def onNewDocument(self, evt):
        self.presenter.onAddBlankDocument(evt=evt)
        self.EndModal(wx.OK)
