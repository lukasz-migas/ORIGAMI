"""Simple dialog to ask for a value in specific format"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog

QUERIES = {
    "charge": ("Assign charge...", 0, "integer", -100, 100),
    "alpha": ("Assign transparency...", 1.0, "float", 0, 1.0),
    "mask": ("Assign mask...", 1.0, "float", 0, 1.0),
    "min_threshold": ("Assign minimum threshold...", 0.0, "float", 0, 1.0),
    "max_threshold": ("Assign maximum threshold...", 1.0, "float", 0, 1.0),
}
KEYWORDS = list(QUERIES.keys())
VALIDATORS = ("integer", "float")


class DialogAsk(Dialog):
    """Simple dialog that will ask what should the new value be."""

    # ui elements
    ok_btn = None
    cancel_btn = None
    input_label = None
    input_value = None

    def __init__(
        self,
        parent,
        item_label: str = None,
        default_value: str = None,
        validator: str = None,
        min_value: float = -100,
        max_value: float = 100,
        keyword: str = None,
    ):
        Dialog.__init__(self, parent, title="Edit parameters...", size=(400, 300))

        # set parameters
        self.parent = parent
        self.return_value = None

        if keyword is not None:
            item_label, default_value, validator, min_value, max_value = QUERIES.get(
                keyword, ("Assign value...", 0, "integer", -100, 100)
            )
        if validator not in VALIDATORS:
            raise ValueError(f"Validator should be an integer or a float and not `{validator}")
        if item_label is None or default_value is None or validator is None:
            raise ValueError("You must provide label or keyword information")

        self.item_label = item_label
        self.item_value = default_value
        self.item_validator = validator
        self.item_min = min_value
        self.item_max = max_value

        # make gui items
        self.make_gui()
        self.SetTitle(item_label)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)
        elif key_code in [wx.WXK_RETURN, 370]:  # enter or enter on numpad
            self.on_ok(None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        self.parent.ask_value = None
        super(DialogAsk, self).on_close(evt, force)

    def on_ok(self, _evt):
        """Close window politely"""
        self.on_apply(evt=None)
        if self.item_validator == "integer":
            self.return_value = int(self.item_value)
        elif self.item_validator == "float":
            self.return_value = float(self.item_value)

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    # noinspection DuplicatedCode
    def make_gui(self):
        """Make UI"""
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
        self.SetSize((350, -1))

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        if self.item_validator == "integer":
            self.input_value = wx.SpinCtrlDouble(
                panel,
                -1,
                value=str(self.item_value),
                min=self.item_min,
                max=self.item_max,
                initial=0,
                inc=1,
                size=(90, -1),
            )
        elif self.item_validator == "float":
            self.input_value = wx.SpinCtrlDouble(
                panel,
                -1,
                value=str(self.item_value),
                min=self.item_min,
                max=self.item_max,
                initial=0,
                inc=0.1,
                size=(90, -1),
            )
        self.input_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.input_value.SetFocus()

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, -1))

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.ok_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.cancel_btn)

        # set controls in a sizer
        sizer = wx.BoxSizer()
        sizer.Add(wx.StaticText(panel, -1, self.item_label), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        sizer.Add(self.input_value, 1, wx.EXPAND)

        # make layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.AddSpacer(10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_apply(self, evt):
        """Update value"""
        self.item_value = self.input_value.GetValue()

        if evt is not None:
            evt.Skip()


if __name__ == "__main__":  # pragma: no cover

    def _main():
        from origami.app import App

        app = App()
        frame = wx.Frame(None, -1)
        ex = DialogAsk(frame, "Assign new value", "0", "integer")
        ex.ShowModal()
        app.MainLoop()

    _main()
