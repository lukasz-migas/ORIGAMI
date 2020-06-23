"""Test PanelAbout dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.misc_notification import Notification

from ..wxtc import WidgetTestCase


class TestNotification(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("flags", (wx.ICON_INFORMATION, wx.ICON_ERROR, wx.ICON_WARNING))
    def test_dialog_ok(self, flags):
        dlg = Notification("ORIGAMI", "Message", flags=flags)

        wx.CallLater(250, dlg.Close, None)
        dlg.Destroy()
        self.yield_()
