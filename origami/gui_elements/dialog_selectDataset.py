import wx


class panelSelectDataset(wx.Dialog):
    """
    """

    def __init__(self, parent, presenter, docList, dataList, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Copy annotations to document/dataset...', size=(400, 300),
                           style=wx.DEFAULT_FRAME_STYLE & ~
                           (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = docList
        self.datasetList = dataList

        # make gui items
        self.make_gui()
        if "set_document" in kwargs:
            self.documentList_choice.SetStringSelection(kwargs['set_document'])
        else:
            self.documentList_choice.SetSelection(0)
        self.onUpdateGUI(None)

        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""

        # If pressed Close, return nothing of value
        self.document = None
        self.dataset = None

        self.Destroy()
    # ----

    def make_gui(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onSelectDocument, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, "Document:")
        self.documentList_choice = wx.ComboBox(panel, -1, choices=self.documentList,
                                               size=(300, -1), style=wx.CB_READONLY)
        self.documentList_choice.Select(0)
        self.documentList_choice.Bind(wx.EVT_COMBOBOX, self.onUpdateGUI)

        datasetList_label = wx.StaticText(panel, -1, "Dataset:")
        self.datasetList_choice = wx.ComboBox(panel, -1, choices=[], size=(300, -1), style=wx.CB_READONLY)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(documentList_label, (0, 0))
        grid.Add(self.documentList_choice, (0, 1), wx.GBSpan(1, 3))
        grid.Add(datasetList_label, (1, 0))
        grid.Add(self.datasetList_choice, (1, 1), wx.GBSpan(1, 3))
        grid.Add(self.okBtn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onUpdateGUI(self, evt):
        document = self.documentList_choice.GetStringSelection()
        spectrum = self.datasetList[document]

        self.datasetList_choice.SetItems(spectrum)
        self.datasetList_choice.SetStringSelection(spectrum[0])

    def onSelectDocument(self, evt):

        document = self.documentList_choice.GetStringSelection()
        dataset = self.datasetList_choice.GetStringSelection()
        self.document = document
        self.dataset = dataset
        self.EndModal(wx.OK)
