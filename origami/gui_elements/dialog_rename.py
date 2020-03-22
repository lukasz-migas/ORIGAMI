# Third-party imports
import wx

# Local imports
from origami.styles import Dialog

FORBIDDEN_NAMES = ["Documents", ""]


class DialogRenameObject(Dialog):
    def __init__(self, parent, presenter, title, **kwargs):
        Dialog.__init__(self, parent, title="Rename...", size=(400, 300))

        self.parent = parent
        self.presenter = presenter
        self.title = title
        self.SetTitle("Document: " + self.title)

        self.new_name = None
        self.kwargs = kwargs

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()

        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

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

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetMinSize((500, 100))

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        BOX_SIZE = 400
        oldName_label = wx.StaticText(panel, -1, "Current name:")
        self.old_name_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, 40), style=wx.TE_READONLY | wx.TE_WORDWRAP)
        self.old_name_value.SetValue(self.kwargs["current_name"])

        newName_label = wx.StaticText(panel, -1, "Edit name:")
        self.new_name_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.new_name_value.SetValue(self.kwargs["current_name"])
        self.new_name_value.SetFocus()

        note_label = wx.StaticText(panel, -1, "Final name:")
        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Rename", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

        # bind
        self.new_name_value.Bind(wx.EVT_TEXT_ENTER, self.on_finish_label_changing)
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_change_label)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # pack elements
        grid = wx.GridBagSizer(5, 5)

        grid.Add(oldName_label, (0, 0))
        grid.Add(self.old_name_value, (0, 1), wx.GBSpan(1, 5))
        grid.Add(newName_label, (1, 0))
        grid.Add(self.new_name_value, (1, 1), wx.GBSpan(1, 5))
        grid.Add(note_label, (2, 0))
        grid.Add(self.note_value, (2, 1), wx.GBSpan(2, 5))

        grid.Add(self.ok_btn, (4, 0), wx.GBSpan(1, 1))
        grid.Add(self.cancel_btn, (4, 1), wx.GBSpan(1, 1))

        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_finish_label_changing(self, evt):
        self.on_change_label(wx.ID_OK)

    def on_change_label(self, evt):
        """ change label of the selected item """

        if self.kwargs["prepend_name"]:
            self.new_name = "{}: {}".format(self.kwargs["current_name"], self.new_name_value.GetValue())
        else:
            self.new_name = "{}".format(self.new_name_value.GetValue())

        if self.new_name in FORBIDDEN_NAMES:
            from origami.gui_elements.misc_dialogs import DialogBox

            DialogBox(
                exceptionTitle="Forbidden name",
                exceptionMsg=f"The name you've selected {self.new_name} is not allowed! Please try again",
                type="Error",
            )
            return

        self.note_value.SetLabel(self.new_name)

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == wx.ID_OK:
            self.Destroy()
