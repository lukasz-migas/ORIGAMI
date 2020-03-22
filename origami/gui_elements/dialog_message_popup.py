# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import make_checkbox


class DialogMessagePopup(Dialog):
    def __init__(self, parent, title, msg, **kwargs):
        Dialog.__init__(self, parent, title="Warning", **kwargs)

        self.make_gui()
        self.CentreOnParent()

        self.msg.SetValue(msg)
        self.SetTitle(title)

        self.ask_again = False

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

        self.msg = wx.TextCtrl(panel, -1, "", size=(400, 40), style=wx.TE_READONLY | wx.TE_WORDWRAP)

        self.yes_btn = wx.Button(panel, wx.ID_ANY, "Yes", size=(-1, 22))
        self.yes_btn.Bind(wx.EVT_BUTTON, self.ok_yes)

        self.no_btn = wx.Button(panel, wx.ID_ANY, "No", size=(-1, 22))
        self.no_btn.Bind(wx.EVT_BUTTON, self.on_no)

        self.ask_again_check = make_checkbox(panel, "Don't ask again")
        self.ask_again_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.msg, (y, 0), wx.GBSpan(1, 4))
        y += 1
        grid.Add(self.yes_btn, (y, 0), flag=wx.ALIGN_CENTER)
        grid.Add(self.no_btn, (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.ask_again_check, (y, 3), flag=wx.ALIGN_CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def ok_yes(self, evt):
        self.EndModal(wx.OK)

    def merge(self, evt):
        self.EndModal(wx.ID_YES)

    def on_no(self, evt):
        self.EndModal(wx.ID_NO)

    def on_apply(self, evt):
        self.ask_again = self.ask_again_check.GetValue()
