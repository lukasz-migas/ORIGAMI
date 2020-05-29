# Third-party imports
import wx

# Local imports
from origami.styles import Dialog


QUERIES = {
    "charge": ("Assign charge...", "integer"),
    "alpha": ("Assign transparency...", "float"),
    "mask": ("Assign mask...", "float"),
    "min_threshold": ("Assign minimum threshold...", "float"),
    "max_threshold": ("Assign maximum threshold...", "float"),
    "label": ("Assign label...", "str"),
}


class DialogAsk(Dialog):
    """Simple dialog that will ask what should the new value be."""

    # ui elements
    ok_btn = None
    cancel_btn = None
    input_label = None
    input_value = None

    def __init__(self, parent, **kwargs):
        Dialog.__init__(self, parent, title="Edit parameters...", size=(400, 300))
        #
        self.parent = parent

        self.item_label = kwargs["static_text"]
        self.item_value = kwargs["value_text"]
        self.item_validator = kwargs["validator"]

        self.return_value = None

        title, _ = QUERIES.get(kwargs["keyword"], ("Assign value...", "str"))
        self.SetTitle(title)

        # make gui items
        self.make_gui()

        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)
        elif key_code in [wx.WXK_RETURN, 370]:  # enter or enter on numpad
            self.on_ok(None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""

        self.parent.ask_value = None
        self.Destroy()

    def on_ok(self, evt):
        self.on_apply(evt=None)

        if self.item_validator == "integer":
            self.return_value = int(self.item_value)
        elif self.item_validator == "float":
            self.return_value = float(self.item_value)
        elif self.item_validator == "str":
            self.return_value = self.item_value

        self.parent.ask_value = self.return_value

        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, "Enter value:")
        self.input_label.SetLabel(self.item_label)
        self.input_label.SetFocus()

        if self.item_validator == "integer":
            self.input_value = wx.SpinCtrlDouble(
                panel, -1, value=str(self.item_value), min=1, max=200, initial=0, inc=1, size=(90, -1)
            )
        elif self.item_validator == "float":
            self.input_value = wx.SpinCtrlDouble(
                panel, -1, value=str(self.item_value), min=0, max=1, initial=0, inc=0.1, size=(90, -1)
            )

        self.input_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)

        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.input_value, (0, 3), flag=wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.ok_btn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancel_btn, (2, 3), wx.GBSpan(1, 1))

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_apply(self, evt):
        self.item_value = self.input_value.GetValue()

        if evt is not None:
            evt.Skip()
