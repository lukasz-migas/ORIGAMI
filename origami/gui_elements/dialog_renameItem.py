import wx


class dialogRenameItem(wx.Dialog):

    def __init__(self, parent, presenter, title, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Rename...', size=(400, 300),
                           style=wx.DEFAULT_FRAME_STYLE & ~
                           (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.title = title
        self.SetTitle('Document: ' + self.title)

        self.new_name = None
        self.kwargs = kwargs
        # make gui items
        self.make_gui()

        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        self.Centre()
        self.Layout()

    # ----

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.new_name = None
        self.Destroy()
    # ----

    def make_gui(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 10)

        # bind
        self.newName_value.Bind(wx.EVT_TEXT_ENTER, self.onFinishLabelChanging)
        self.okBtn.Bind(wx.EVT_BUTTON, self.onChangeLabel)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetMinSize((500, 100))

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        BOX_SIZE = 400
        oldName_label = wx.StaticText(panel, -1, "Current name:")
        self.oldName_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, 40),
                                         style=wx.TE_READONLY | wx.TE_WORDWRAP)
        self.oldName_value.SetValue(self.kwargs['current_name'])

        newName_label = wx.StaticText(panel, -1, "Edit name:")
        self.newName_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.newName_value.SetValue(self.kwargs['current_name'])
        self.newName_value.SetFocus()

        note_label = wx.StaticText(panel, -1, "Final name:")
        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Rename", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)

        grid.Add(oldName_label, (0, 0))
        grid.Add(self.oldName_value, (0, 1), wx.GBSpan(1, 5))
        grid.Add(newName_label, (1, 0))
        grid.Add(self.newName_value, (1, 1), wx.GBSpan(1, 5))
        grid.Add(note_label, (2, 0))
        grid.Add(self.note_value, (2, 1), wx.GBSpan(2, 5))

        grid.Add(self.okBtn, (4, 0), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (4, 1), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onFinishLabelChanging(self, evt):
        self.onChangeLabel(wx.ID_OK)

    def onChangeLabel(self, evt):
        """ change label of the selected item """

        if self.kwargs['prepend_name']:
            self.new_name = "{}: {}".format(self.kwargs['current_name'], self.newName_value.GetValue())
        else:
            self.new_name = "{}".format(self.newName_value.GetValue())
        self.note_value.SetLabel(self.new_name)

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == wx.ID_OK:
            self.Destroy()
