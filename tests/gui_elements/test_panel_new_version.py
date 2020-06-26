"""Test PanelNewVersion dialog"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.panel_notify_new_version import PanelNewVersion

from ..wxtc import WidgetTestCase


class TestPanelNewVersion(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelNewVersion(self.frame)

        assert dlg.not_ask_again_check.GetValue() is CONFIG.new_version_panel_do_not_ask
        assert dlg.search_bar.IsEnabled() is False

        # wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()
