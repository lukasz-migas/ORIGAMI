"""Notify user of open documents"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog


class DialogNotifyOpenDocuments(Dialog):
    """Notification dialog to let the user know that some documents are still open and work might be lost"""

    save_all_btn = None
    continue_btn = None
    cancel_btn = None

    def __init__(self, parent, message: str = None):
        Dialog.__init__(self, parent, title="Documents are still open...!")

        self.parent = parent

        if message is None:
            message = (
                "Few document(s) are still open and you might lose some work if they are not saved."
                "\nAre you sure you would want to continue?"
            )

        self.message = message

        self.make_gui()
        self.CentreOnParent()

    def on_ok(self, _evt):
        """Politely close window without saving document"""
        self.EndModal(wx.ID_OK)

    def on_save_documents(self, _evt):
        """Save all documents"""
        self.EndModal(wx.ID_SAVE)

    def make_gui(self):
        """Make UI"""
        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def make_panel(self):
        """Make panel"""

        panel = wx.Panel(self, -1)

        self.save_all_btn = wx.Button(panel, -1, "Save all", size=(-1, 22))
        self.save_all_btn.Bind(wx.EVT_BUTTON, self.on_save_documents)

        self.continue_btn = wx.Button(panel, wx.ID_OK, "Continue without saving", size=(-1, 22))
        self.continue_btn.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close, id=wx.ID_CANCEL)
        self.cancel_btn.SetFocus()

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.save_all_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.continue_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.cancel_btn)

        # make layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(wx.StaticText(panel, -1, self.message), 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel


def _main():

    app = wx.App()
    ex = DialogNotifyOpenDocuments(None)

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
