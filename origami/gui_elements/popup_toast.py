"""Toast-like message that shows on top of the frame and is dismissed after N seconds"""
# Third-party imports
import wx

# Local imports
from origami.styles import set_item_font
from origami.icons.assets import Icons
from origami.gui_elements.popup import PopupBase
from origami.gui_elements._panel import TestPanel  # noqa

POPUP_TOAST_STYLES = ["info", "success", "warning", "error"]


class PopupToast(PopupBase):
    """Popup toast"""

    INFO_MESSAGE = "This popup window will automatically close after a few seconds."
    ENABLE_RIGHT_CLICK_DISMISS = False
    ENABLE_LEFT_DLICK_DISMISS = False
    ENABLE_MOVE = False
    TEXT_COLOR = wx.WHITE

    text = None

    def __init__(self, parent, message: str, kind: str, timeout: int = 3000, icons: Icons = None, style=wx.BORDER_NONE):
        if icons is None:
            icons = Icons()
        self._icons = icons
        self.message = message
        self.kind = kind

        PopupBase.__init__(self, parent, style)
        self.set_kind(kind)

        # setup dismiss timer
        self.timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self.on_dismiss, self.timer)
        self.timer.StartOnce(timeout)

    def make_panel(self):
        """Make panel"""

        self.text = wx.StaticText(self, -1, self.message, style=wx.ALIGN_CENTER_HORIZONTAL)
        set_item_font(self.text, 12)
        self.text.SetForegroundColour(self.TEXT_COLOR)
        self.text.Wrap(325)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.text, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
        sizer.AddSpacer(5)

        sizer.Fit(self)
        self.SetSizerAndFit(sizer)
        self.SetSize(350, -1)
        self.Layout()

    def set_kind(self, kind):
        """Set frame color based on the type of message"""
        color, font_color = {
            "info": ("#007bff", wx.WHITE),
            "success": ("#28a745", wx.WHITE),
            "warning": ("#fd7e14", wx.WHITE),
            "error": ("#dc3545", wx.WHITE),
        }.get(kind.lower(), ("#007bff", wx.WHITE))
        self.SetBackgroundColour(color)
        self.text.SetForegroundColour(font_color)


class PopupToastManager:
    """Manager of popup toasts"""

    VERTICAL_OFFSET = 10
    popups = []
    counter = 0

    def __init__(self, parent):
        self.parent = parent
        self._icons = Icons()

    def _check_popups(self):
        """Check previous popups"""
        if not self.popups:
            return 0, 0

        move_h, move_v = 0, 0
        for popup in reversed(self.popups):
            if popup:
                _size_h, _size_v = popup.GetSize()
                move_v += _size_v + self.VERTICAL_OFFSET
            else:
                self.popups.remove(popup)
                self.counter -= 1

        return move_h, move_v

    def show_popup(self, message: str, kind: str, timeout: int = 3000):
        """Add popup window"""
        p = PopupToast(self.parent, message, kind, timeout)
        move_h, move_v = self._check_popups()
        p.position_on_window(self.parent, move_h, move_v)
        p.Show()

        self.popups.append(p)
        self.counter += 1


class TestPopup(TestPanel):
    """Test the popup window"""

    def __init__(self, parent):
        super().__init__(parent)

        self.SetSize((800, 800))
        self.manager = PopupToastManager(self)

        self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

    def on_popup(self, _evt):
        """Activate popup"""
        self.manager.show_popup("This is some nice testing text.\nAnd some more text ", "info")
        self.manager.show_popup("This is some nice testing text.\nAnd some more text ", "success")
        self.manager.show_popup("This is some nice testing text.\nAnd some more text ", "warning")
        self.manager.show_popup("This is some nice testing text.\nAnd some more text ", "error")


def _main_popup():

    app = wx.App()

    dlg = TestPopup(None)
    wx.PostEvent(dlg.btn_1, wx.PyCommandEvent(wx.EVT_BUTTON.typeId, dlg.btn_1.GetId()))
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main_popup()
