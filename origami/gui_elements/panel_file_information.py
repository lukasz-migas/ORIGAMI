# Third-party imports
import wx

# Local imports
from origami.gui_elements.popup import TransientPopupBase
from origami.gui_elements._panel import TestPanel


class PanelInformationPopup(TransientPopupBase):
    """Create popup window to modify few uncommon settings"""

    information = None

    def __init__(self, parent, message: str, style=wx.BORDER_SIMPLE):
        TransientPopupBase.__init__(self, parent, style)
        self.information.SetLabel(message)

    def make_panel(self):
        """Make popup window"""
        self.information = wx.StaticText(self, -1, "", size=(400, 200), style=wx.ALIGN_LEFT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.information, 1, wx.EXPAND | wx.ALL, 20)

        self.SetSizerAndFit(sizer)
        self.Layout()


def _main():

    from origami.app import App

    class TestInformation(TestPanel):
        """Test the popup window"""

        def __init__(self, parent):
            super().__init__(parent)

            self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

        def on_popup(self, evt):
            """Activate popup"""
            p = PanelInformationPopup(self, "Document: Document 1\nRaw file: PATH")
            p.position_on_event(evt)
            p.Show()

    app = App()

    dlg = TestInformation(None)
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
