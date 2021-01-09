"""Simple dialog that gives the user quick selection window"""
# Standard library imports
from typing import List

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.gui_elements.helpers import set_tooltip


class DialogQuickSelection(Dialog):
    """Simple dialog to ask whether to overwrite, merge or duplicate object"""

    # ui elements
    msg = None
    choice_value = None
    ok_btn = None
    close_btn = None

    def __init__(self, parent, options: List[str], msg: str = None):
        Dialog.__init__(self, parent, title="Quick selection")

        self.parent = parent
        if msg is None:
            msg = "Please select from one of the options below."

        self._msg = msg
        self.options = options
        self.value = None

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

        self.choice_value = wx.Choice(panel, -1, choices=self.options, size=(-1, -1))
        self.choice_value.SetSelection(0)
        self.choice_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Accept current selection and close this window.")

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, -1))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.close_btn, "Close this window and perform no action.")

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.ok_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.close_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.msg, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(self.choice_value, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_ok(self, evt):
        """Close window in tidy manner"""
        self.value = self.choice_value.GetStringSelection()
        super(DialogQuickSelection, self).on_ok(evt)

    def on_close(self, evt, force: bool = False):
        """Close window with ID_NO event"""
        self.value = None

        super(DialogQuickSelection, self).on_close(evt, force)

    def on_apply(self, _evt):
        """Apply changes"""
        self.value = self.choice_value.GetStringSelection()


def _main():

    from origami.app import App

    app = App()
    frame = wx.Frame(None, -1)
    ex = DialogQuickSelection(frame, ["Option 1", "Option 2"])
    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
