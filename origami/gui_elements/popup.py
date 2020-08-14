"""Popup"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_bitmap_btn


class PopupMixin:
    """Mixin class to reduce number of duplicated functions for the popup elements"""

    ld_pos = None
    w_pos = None
    title = None

    ENABLE_MOVE = True
    ENABLE_RIGHT_CLICK_DISMISS = True
    ENABLE_LEFT_DLICK_DISMISS = True
    ENABLE_INFO_MESSAGE = True
    TEXT_COLOR = wx.BLACK
    INFO_MESSAGE = "Right-click inside the popup window to close it."

    def on_dismiss(self, _evt):
        """Dismiss window"""
        self.Show(False)  # noqa
        wx.CallAfter(self.Destroy)  # noqa

    def get_info(self):
        """Return text item with information on how to dismiss the window"""
        text = wx.StaticText(self, -1, self.INFO_MESSAGE)
        text.SetForegroundColour(self.TEXT_COLOR)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
        sizer.Add(text, 1, wx.EXPAND)
        return sizer

    def set_info(self, sizer):
        """Set info in the popup"""
        if not self.ENABLE_INFO_MESSAGE:
            return
        text = wx.StaticText(self, -1, self.INFO_MESSAGE)
        text.SetForegroundColour(self.TEXT_COLOR)

        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
        sizer.Add(text, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 2)

    def set_title(self, title: str):
        """Set title in the popup window"""
        if self.title is not None:
            self.title.SetLabel(title)

    def set_close_btn(self, sizer):
        """Set exit button in the popup window"""
        icon = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON, wx.Size(24, 24))
        close_btn = make_bitmap_btn(self, wx.ID_ANY, icon, style=wx.BORDER_NONE)
        close_btn.Bind(wx.EVT_BUTTON, self.on_dismiss)

        self.title = wx.StaticText(self, -1, "")

        _sizer = wx.BoxSizer()
        _sizer.Add(self.title, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
        _sizer.AddStretchSpacer()
        _sizer.Add(close_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

        sizer.Insert(0, _sizer, 0, wx.EXPAND | wx.ALL, 2)

    def on_key_event(self, evt):
        """Capture keyboard events"""
        key_code = evt.GetKeyCode()

        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.Destroy()  # noqa

        evt.Skip()

    def position_on_event(self, evt, move_h: int = 0, move_v: int = 0):
        """Position the window on an event location

        Parameters
        ----------
        evt : event
            wxPython event
        move_h : int
            horizontal offset to move the popup to the side
        move_v : int
            vertical offset to move the popup up or down
        """
        obj = evt.GetEventObject()
        if hasattr(obj, "ClientToScreen"):
            pos = obj.ClientToScreen((0, 0))  # noqa
        else:
            pos = (0, 0)
        pos = (pos[0] - move_h, pos[1] - move_v)
        self.SetPosition(pos)  # noqa

    def position(self, x, y):
        """Simply set position of the window"""
        self.SetPosition((x, y))  # noqa

    def position_on_window(self, window, move_h: int = 0, move_v: int = 0):
        """Position the window on the window position"""
        # get current position of the window
        x, y = window.GetPosition()
        # get current size of the window
        dx, dy = window.GetSize()
        # get current size of the popup
        px, py = self.GetSize()  # noqa
        x = x + dx - px - move_h - 25
        y = y + dy - py - move_v - 25
        print(x, y)
        self.SetPosition((x, y))  # noqa

    def position_on_mouse(self, move_h: int = 0, move_v: int = 0):
        """Position the window on the last mouse position"""
        pos = wx.GetMousePosition()
        pos = (pos[0] - move_h, pos[1] - move_v)
        self.SetPosition(pos)  # noqa

    def on_mouse_left_down(self, evt):
        """On left-click event"""
        self.Refresh()  # noqa
        self.ld_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.w_pos = self.ClientToScreen((0, 0))  # noqa
        self.CaptureMouse()  # noqa

    def on_mouse_left_up(self, _evt):
        """On left-release event"""
        if self.HasCapture():  # noqa
            self.ReleaseMouse()  # noqa

    def on_move(self, evt):
        """On move event"""
        if evt.Dragging() and evt.LeftIsDown() and self.w_pos is not None and self.ld_pos is not None:
            d_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            new_pos = (self.w_pos.x + (d_pos.x - self.ld_pos.x), self.w_pos.y + (d_pos.y - self.ld_pos.y))
            self.Move(new_pos)  # noqa


class PopupBase(wx.PopupWindow, PopupMixin):
    """Create popup window to modify few uncommon settings"""

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        wx.PopupWindow.__init__(self, parent, style)
        self.make_panel()

        if self.ENABLE_MOVE:
            self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
            self.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
            self.Bind(wx.EVT_MOTION, self.on_move)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        if self.ENABLE_RIGHT_CLICK_DISMISS:
            self.Bind(wx.EVT_RIGHT_UP, self.on_dismiss)
        if self.ENABLE_LEFT_DLICK_DISMISS:
            self.Bind(wx.EVT_LEFT_DCLICK, self.on_dismiss)

    def make_panel(self):
        """Make popup window"""
        raise NotImplementedError("Must implement method")


class TransientPopupBase(wx.PopupTransientWindow, PopupMixin):
    """Create popup window to modify few uncommon settings"""

    ld_pos = None
    w_pos = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        wx.PopupTransientWindow.__init__(self, parent, style)

        self.make_panel()

        if self.ENABLE_MOVE:
            self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
            self.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
            self.Bind(wx.EVT_MOTION, self.on_move)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        if self.ENABLE_RIGHT_CLICK_DISMISS:
            self.Bind(wx.EVT_RIGHT_UP, self.on_dismiss)
        if self.ENABLE_LEFT_DLICK_DISMISS:
            self.Bind(wx.EVT_LEFT_DCLICK, self.on_dismiss)

    def Dismiss(self):
        """Dismiss window"""
        super(TransientPopupBase, self).Dismiss()

    def make_panel(self):
        """Make popup window"""
        raise NotImplementedError("Must implement method")
