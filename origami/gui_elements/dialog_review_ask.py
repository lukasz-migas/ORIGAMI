"""Simple dialog to ask whether to overwrite, merge or duplicate object"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.gui_elements.helpers import set_tooltip


class DialogAskReview(Dialog):
    """Simple dialog to ask whether to overwrite, merge or duplicate object"""

    # ui elements
    msg = None
    review_btn = None
    continue_btn = None
    close_btn = None

    def __init__(self, parent, msg: str = None):
        Dialog.__init__(self, parent, title="Conflicting name...")

        self.parent = parent
        if msg is None:
            msg = (
                "There are object(s) in the clipboard. Closing window without applying changes will delete them. "
                "\nWhat would you like to do?"
            )

        self._msg = msg
        self.action = None

        self.make_gui()
        self.CentreOnParent()

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize((-1, -1))

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        self.msg = wx.StaticText(panel, -1, self._msg, size=(-1, -1))

        self.review_btn = wx.Button(panel, wx.ID_ANY, "Review", size=(-1, -1))
        self.review_btn.Bind(wx.EVT_BUTTON, self.review)
        set_tooltip(self.review_btn, "Review clipboard data before closing the window.")

        self.continue_btn = wx.Button(panel, wx.ID_ANY, "Continue", size=(-1, -1))
        self.continue_btn.Bind(wx.EVT_BUTTON, self.ok)
        set_tooltip(self.continue_btn, "Continue without reviewing clipboard data.")

        self.close_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, -1))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.close_btn, "Cancel action and come back to the main window.")

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.review_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.continue_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.close_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.msg, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def review(self, _evt):
        """Overwrite existing"""
        self.action = "review"
        self.on_ok(wx.ID_SAVE)

    def ok(self, _evt):
        """Merge existing"""
        self.action = "continue"
        self.on_ok(wx.ID_YES)

    def on_ok(self, evt):
        """Close window in tidy manner"""
        if self.IsModal():
            self.EndModal(evt)
        else:
            self.Destroy()

    def on_close(self, _evt, force: bool = False):
        """Close window with ID_NO event"""
        self.action = None

        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()


def _main():

    from origami.app import App

    app = App()
    frame = wx.Frame(None, -1)
    ex = DialogAskReview(frame)
    res = ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
