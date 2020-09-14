"""Annotations settings popup"""
# Third-party imports
import wx

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.gui_elements.helpers import set_tooltip


class DialogAutoGenerateConformers(MiniFrame):
    """Create popup window to modify few uncommon settings"""

    mw_value, charge_start, charge_end, mz_window, ok_btn, simulate_btn = None, None, None, None, None, None

    def __init__(self, parent):
        MiniFrame.__init__(self, parent, title="Auto-generate calibrants")

        # make gui items
        self.make_gui()

    def make_panel(self):
        """Make popup window"""
        panel = wx.Panel(self, -1)

        self.mw_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        set_tooltip(self.mw_value, "Approximate molecular weight of the calibrant.")

        self.mz_window = wx.TextCtrl(panel, -1, "25", validator=Validator("floatPos"))
        set_tooltip(
            self.mz_window,
            "This window will be applied around each of the simulated m/z values. The calculation is based on the"
            " molecular weight filled-in above and the range of charges filled-in below.",
        )

        self.charge_start = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        set_tooltip(self.charge_start, "The lower charge state which should be used to guess the m/z value in the MS")

        self.charge_end = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        set_tooltip(self.charge_end, "The upper charge state which should be used to guess the m/z value in the MS")

        self.simulate_btn = wx.Button(panel, -1, "Simulate")
        self.simulate_btn.Bind(wx.EVT_BUTTON, self.on_simulate)
        set_tooltip(
            self.simulate_btn, "Display the suggested m/z windows in the mass spectrum without extracting any data"
        )

        self.ok_btn = wx.Button(panel, -1, "Process")
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(
            self.ok_btn,
            "Extract mobilogram data for each of the suggested m/z windows, find the apex and add it to "
            " the table. Make sure to change the value of CCS since its preset with`1`",
        )

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(wx.StaticText(panel, -1, "MW (Da)"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "m/z window:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_window, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Charge (start):"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_start, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "Charge (end):"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_end, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.simulate_btn)
        btn_sizer.AddSpacer(3)
        btn_sizer.Add(self.ok_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def _get_data(self):
        mw = str2num(self.mw_value.GetValue())
        mz_window = str2num(self.mz_window.GetValue())
        z_start = str2int(self.charge_start.GetValue())
        z_end = str2int(self.charge_end.GetValue())
        if not all([mw, mz_window, z_start, z_end]):
            raise MessageError("Error", "All values must be greater than 0")

        return mw, z_start, z_end, mz_window

    def on_simulate(self, _evt):
        """Simulate data processing"""
        mw, z_start, z_end, mz_window = self._get_data()

        # auto-generate conformers
        if hasattr(self.parent, "_simulate_auto_process"):
            self.parent._simulate_auto_process(mw, z_start, z_end, mz_window)  # noqa

    def on_ok(self, _evt):
        """Process data"""
        mw, z_start, z_end, mz_window = self._get_data()

        # auto-generate conformers
        if hasattr(self.parent, "_on_auto_process"):
            self.parent._on_auto_process(mw, z_start, z_end, mz_window)  # noqa


def _main_popup():
    from origami.gui_elements._panel import TestPanel  # noqa

    class TestPopup(TestPanel):
        """Test the popup window"""

        def __init__(self, parent):
            super().__init__(parent)

            self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

        def on_popup(self, _evt):
            """Activate popup"""

            p = DialogAutoGenerateConformers(self)
            p.Show()

    app = wx.App()
    dlg = TestPopup(None)
    wx.PostEvent(dlg.btn_1, wx.PyCommandEvent(wx.EVT_BUTTON.typeId, dlg.btn_1.GetId()))
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main_popup()
