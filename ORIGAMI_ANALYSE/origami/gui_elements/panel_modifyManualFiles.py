import wx

from icons import IconContainer as icons
from styles import makeCheckbox, validator
from utils.converters import num2str


class panelModifyManualFiles(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Modify settings...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons()
        self.importEvent = False

        self.SetTitle(kwargs.get('document', "filename"))
        self.itemInfo = kwargs

        # check values
        if self.itemInfo['energy'] in ['', None, 'None']:
            self.itemInfo['energy'] = ""

        if self.itemInfo['color'][0] == -1:
            self.itemInfo['color'] = (1, 1, 1, 255)

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keyboard_event)

        # fire-up events
        self.on_setup_gui(evt=None)
    # ----

    def on_keyboard_event(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.on_close(evt=None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        check_label = wx.StaticText(panel, wx.ID_ANY, "Check:")
        self.check_value = makeCheckbox(panel, "")
        self.check_value.Bind(wx.EVT_CHECKBOX, self.on_apply)

        document_label = wx.StaticText(panel, wx.ID_ANY, "Document:")
        self.document_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        filename_label = wx.StaticText(panel, wx.ID_ANY, "Filename:")
        self.filename_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY, "Label:", wx.DefaultPosition,
                                    wx.DefaultSize, wx.ALIGN_LEFT)
        self.label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.label_value.SetValue(self.itemInfo['label'])
        self.label_value.Bind(wx.EVT_TEXT, self.on_apply)

        variable_label = wx.StaticText(panel, wx.ID_ANY, "Variable:")
        self.variable_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.variable_value.SetValue(self.itemInfo['energy'])
        self.variable_value.Bind(wx.EVT_TEXT, self.on_apply)

        color_label = wx.StaticText(panel, -1, "Color:")
        self.color_value = wx.Button(panel, wx.ID_ANY, "", wx.DefaultPosition,
                                          wx.Size(26, 26), 0)
        self.color_value.SetBackgroundColour(self.itemInfo['color'])
        self.color_value.Bind(wx.EVT_BUTTON, self.on_assign_color)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.showBtn = wx.Button(panel, wx.ID_OK, "Show", size=(-1, 22))
        self.previousBtn = wx.Button(panel, wx.ID_OK, "Previous", size=(-1, 22))
        self.nextBtn = wx.Button(panel, wx.ID_OK, "Next", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))

        self.showBtn.Bind(wx.EVT_BUTTON, self.on_show)
        self.nextBtn.Bind(wx.EVT_BUTTON, self.on_get_next)
        self.previousBtn.Bind(wx.EVT_BUTTON, self.on_get_previous)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.showBtn, (n, 0), wx.GBSpan(1, 1))
        btn_grid.Add(self.previousBtn, (n, 1), wx.GBSpan(1, 1))
        btn_grid.Add(self.nextBtn, (n, 2), wx.GBSpan(1, 1))
        btn_grid.Add(self.cancelBtn, (n, 3), wx.GBSpan(1, 1))

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(check_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.check_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(document_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.filename_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(variable_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.variable_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(color_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def on_apply(self, evt):
#         self.on_check_id()
        pass

    def on_get_next(self, evt):
        pass

    def on_get_previous(self, evt):
        pass

    def on_check_id(self, evt):
        pass

    def on_show(self, evt):
        pass

    def on_setup_gui(self, evt):
        pass

    def on_update_gui(self, evt):
        pass

    def on_toggle_controls(self, evt):
        pass

    def on_assign_color(self, evt):
        pass
#         pass
#         self.on_check_id()
#         if evt:
#             color = self.parent.on_assign_color(evt=None,
#                                               itemID=self.itemInfo['id'],
#                                               give_value=True)
#             self.origami_color_value.SetBackgroundColour(color)
#         else:
#             color = self.origami_color_value.GetBackgroundColour()
#             self.parent.peaklist.SetItemBackgroundColour(self.itemInfo['id'], color)
