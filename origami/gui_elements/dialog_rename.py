"""Simple panel used to rename elements"""
# Standard library imports
from typing import List

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import set_tooltip

FORBIDDEN_NAMES = ["Documents", ""]
BOX_SIZE = 400


class DialogRenameObject(Dialog):
    """Simple dialog to rename object"""

    # ui elements
    old_name_value = None
    new_name_value = None
    note_value = None
    ok_btn = None
    cancel_btn = None

    def __init__(self, parent, current_name: str, prepend_name: str = "", forbidden: List[str] = None):
        Dialog.__init__(self, parent, title="Rename...", size=(400, 300))

        self.parent = parent
        self.current_name = current_name
        self.prepend_name = prepend_name
        self.new_name = None

        if forbidden is None:
            forbidden = FORBIDDEN_NAMES
        self.forbidden = forbidden

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.on_new_name(None)

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        self.new_name = None
        super(DialogRenameObject, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetMinSize((500, 100))

    def make_panel(self):
        """Make panel"""

        panel = wx.Panel(self, -1)

        self.old_name_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.old_name_value.SetLabel(self.current_name)
        set_tooltip(self.old_name_value, "Current name of the object.")

        self.new_name_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.new_name_value.SetValue(self.current_name)
        self.new_name_value.Bind(wx.EVT_TEXT, self.on_new_name)
        self.new_name_value.SetFocus()
        set_tooltip(
            self.new_name_value,
            "Type-in new name of the object. If the box is glowing red, it indicates that the selected name is"
            " not allowed.",
        )

        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)
        set_tooltip(self.note_value, "Final name of the object after you click on `Rename` button")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Rename", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Rename object to the `New name` value.")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close window and do not rename the object.")

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.ok_btn)
        btn_sizer.AddSpacer(10)
        btn_sizer.Add(self.cancel_btn)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(wx.StaticText(panel, -1, "Current name:"), (0, 0), flag=wx.ALIGN_TOP)
        grid.Add(self.old_name_value, (0, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, -1, "New name:"), (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.new_name_value, (1, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)

        grid.Add(wx.StaticLine(panel, wx.SL_HORIZONTAL), (2, 0), (1, 6), flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, -1, "Final name:"), (3, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.note_value, (3, 1), wx.GBSpan(2, 5), flag=wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_new_name(self, _evt):
        """Finish editing label"""
        new_name = self.set_new_name

        if new_name in self.forbidden:
            self.new_name_value.SetBackgroundColour((255, 230, 239))
            self.note_value.SetLabel("This name is not allowed")
        else:
            self.new_name_value.SetBackgroundColour(wx.WHITE)
            self.note_value.SetLabel(new_name)
        self.new_name_value.Refresh()

    @property
    def set_new_name(self):
        """Return `new_name`"""
        if self.prepend_name:
            self.new_name = "{}: {}".format(self.current_name, self.new_name_value.GetValue())
        else:
            self.new_name = "{}".format(self.new_name_value.GetValue())

        return self.new_name

    def on_ok(self, _evt):
        """ change label of the selected item """
        if self.new_name in self.forbidden:
            from origami.gui_elements.misc_dialogs import DialogBox

            DialogBox(
                title="Forbidden name",
                msg=f"The name you've selected {self.new_name} is not allowed! Please type-in another name.",
                kind="Error",
                parent=self,
            )
            return

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()


def _main():
    app = wx.App()
    ex = DialogRenameObject(None, "Current name")

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
