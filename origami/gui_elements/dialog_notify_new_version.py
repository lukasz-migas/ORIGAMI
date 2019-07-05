# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from ids import ID_helpNewVersion
from styles import Dialog


class DialogNewVersion(Dialog):

    def __init__(self, parent, **kwargs):
        Dialog.__init__(self, parent, title='New version of ORIGAMI is available!')

        self.parent = parent
        self.presenter = kwargs['presenter']
        self.icons = self.presenter.icons
        self.message = kwargs['webpage']

        self.make_gui()
        self.CentreOnParent()
        self.Show(True)
        self.SetFocus()
        self.Raise()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def onOK(self, evt):

        self.presenter.on_open_weblink(evt)
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.goToDownload.Bind(wx.EVT_BUTTON, self.onOK, id=ID_helpNewVersion)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)

        self.label_header = wx.html.HtmlWindow(
            panel,
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.html.HW_SCROLLBAR_AUTO,
            size=(500, 400),
        )
        self.label_header.SetPage(self.message)

        self.goToDownload = wx.Button(panel, ID_helpNewVersion, 'Download Now', size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, 'Cancel', size=(-1, 22))

        btn_grid = wx.GridBagSizer(1, 1)
        btn_grid.Add(self.goToDownload, (0, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)
        btn_grid.Add(self.cancelBtn, (0, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(image, (0, 0), wx.GBSpan(1, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(horizontal_line_1, (1, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        grid.Add(
            self.label_header, (2, 0), wx.GBSpan(2, 3), flag=wx.EXPAND |
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        grid.Add(horizontal_line_2, (4, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        grid.Add(btn_grid, (5, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel
