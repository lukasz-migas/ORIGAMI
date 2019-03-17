import wx


class panelInformation(wx.MiniFrame):
    """
    """

    def __init__(self, parent, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Sample information', size=(300, 200),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)

        self.parent = parent

        # make gui items
        self.makeGUI()

        self.Centre()
        self.SetSize((450, 140))
        self.Layout()
        self.SetFocus()

        if "title" in kwargs:
            self.SetTitle(kwargs['title'])

        if "information" in kwargs:
            self.information.SetLabel(kwargs['information'])
            self.information.Wrap(425)

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
    # ----

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()

        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)

        evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # make editor
        self.information = wx.StaticText(panel, -1, "", size=(-1, -1))

        # make buttons
        self.okBtn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.okBtn.Bind(wx.EVT_BUTTON, self.onClose)

        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.okBtn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.information, (0, 0), wx.GBSpan(4, 8), flag=wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(btn_grid, (4, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

