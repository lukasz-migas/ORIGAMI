"""Test PanelAbout dialog"""
# Local imports
from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

from ..wxtc import WidgetTestCase


class TestPanelHTMLViewer(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelHTMLViewer(self.frame, link="www.google.com")

        # wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        # self.yield_()
