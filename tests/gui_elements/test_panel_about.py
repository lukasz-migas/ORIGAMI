"""Test PanelAbout dialog"""
# Third-party imports
import wx

# Local imports
from origami.icons.icons import IconContainer
from origami.gui_elements.panel_about import PanelAbout

from ..wxtc import WidgetTestCase


class TestPanelAbout(WidgetTestCase):
    """Test dialog"""

    def test_dialog_close(self):
        icons = IconContainer()

        dlg = PanelAbout(self.frame, icons)

        wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        dlg.Destroy()
        self.yield_()
