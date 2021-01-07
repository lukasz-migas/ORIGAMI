"""Dialog to select x/y-axis labels"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog


# noinspection DuplicatedCode
class DialogSelectLabels(Dialog):
    """Dialog window to select x/y-axis labels"""

    # ui elements
    msg = None
    x_label_combo = None
    x_label_enter = None
    y_label_combo = None
    y_label_enter = None
    ok_btn = None
    cancel_btn = None

    _x_label_value = "Scans"
    _y_label_value = "Drift time (bins)"

    LABEL_CHOICES = [
        "Scans",
        "Time (min)",
        "Retention time (min)",
        "Collision Voltage (V)",
        "Activation Voltage (V)",
        "Activation Energy (eV)",
        "Lab Frame Energy (eV)",
        "Drift time (bins)",
        "Drift time (ms)",
        "Collision Cross Section (Å²)",
        "Mass-to-charge (Da)",
        "m/z (Da)",
        "Charge",
        "Wavenumber (cm⁻¹)",
        "Other...",
    ]
    X_LABEL_DEFAULT = "Scans"
    Y_LABEL_DEFAULT = "Drift time (bins)"

    def __init__(self, parent, msg=None, **kwargs):
        Dialog.__init__(self, parent, title="Please select x/y-labels", **kwargs)

        self.parent = parent
        self.make_gui()
        self.CentreOnParent()

        if msg is None:
            msg = (
                "Please select x- and y-axis labels for the dataset(s)."
                "\nIf multiple datasets are loaded at the same time, the"
                "\nsame label will be associated with each dataset."
                "\nLabels can be changed at any point when"
                "\nanalysing data in ORIGAMI."
            )
        self.msg.SetLabel(msg)

        self.setup()

    def make_gui(self):
        """Make UI"""
        self.make_panel()
        self.SetSize((350, -1))

    def make_panel(self):
        """Make panel"""
        # panel = wx.Panel(self, -1)
        self.msg = wx.StaticText(self, -1, "", size=(-1, -1))
        self.msg.SetFont(self.msg.GetFont().Larger())

        self.x_label_combo = wx.ComboBox(self, -1, choices=self.LABEL_CHOICES, style=wx.CB_READONLY)
        self.x_label_combo.SetStringSelection(self.X_LABEL_DEFAULT)
        self.x_label_combo.Bind(wx.EVT_COMBOBOX, self.on_select)

        self.x_label_enter = wx.TextCtrl(self, -1, "")
        self.x_label_combo.Bind(wx.EVT_TEXT, self.on_select)

        self.y_label_combo = wx.ComboBox(self, -1, choices=self.LABEL_CHOICES, style=wx.CB_READONLY)
        self.y_label_combo.SetStringSelection(self.Y_LABEL_DEFAULT)
        self.y_label_combo.Bind(wx.EVT_COMBOBOX, self.on_select)

        self.y_label_enter = wx.TextCtrl(self, -1, "")
        self.y_label_enter.Bind(wx.EVT_TEXT, self.on_select)

        self.ok_btn = wx.Button(self, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(self, wx.ID_ANY, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.ok_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.cancel_btn)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(wx.StaticText(self, -1, "X-axis label:"), (y, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.x_label_combo, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(self.x_label_enter, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Y-axis label:"), (y, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.y_label_combo, (y, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(self.y_label_enter, (y, 1), flag=wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.msg, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.AddSpacer(10)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.AddSpacer(10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)

    def setup(self):
        """Setup text input"""
        show_x = self._x_label_value == "Other..."
        self.x_label_enter.Enable(show_x)

        show_y = self._y_label_value == "Other..."
        self.y_label_enter.Enable(show_y)

    def on_ok(self, _):
        """Exit politely"""
        self._x_label_value, self._y_label_value = self.get_labels()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_close(self, _evt, force: bool = False):
        """Close window"""
        self._x_label_value = None
        self._y_label_value = None

        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    @property
    def x_label(self):
        """Return x-axis label"""
        return self._x_label_value

    @property
    def y_label(self):
        """Return y-axis label"""
        return self._y_label_value

    @property
    def xy_labels(self):
        """Return x/y-axis labels"""
        return self.x_label, self.y_label

    def on_select(self, _):
        """Update user selection"""
        self._x_label_value = self.x_label_combo.GetStringSelection()
        self._y_label_value = self.y_label_combo.GetStringSelection()
        self.setup()

    def get_labels(self):
        """Actually decide which labels the user has selected"""
        x_label_value = self._x_label_value
        y_label_value = self._y_label_value

        if x_label_value == "Other...":
            x_label_value = self.x_label_enter.GetValue()

        if y_label_value == "Other...":
            y_label_value = self.y_label_enter.GetValue()
        return x_label_value, y_label_value


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        app = App()
        frame = wx.Frame(None, -1)
        ex = DialogSelectLabels(frame)
        ex.ShowModal()
        app.MainLoop()

    _main()
