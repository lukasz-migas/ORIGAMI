"""Test PanelNewVersion dialog"""
# Standard library imports
import sys

# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.config.config import CONFIG
from origami.gui_elements.panel_notify_new_version import PanelNewVersion


@pytest.mark.guitest
@pytest.mark.skipif(sys.platform == "win32", reason="Running this test under Windows can sporadically cause errors")
class TestPanelNewVersion(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelNewVersion(self.frame)

        assert dlg.not_ask_again_check.GetValue() is CONFIG.new_version_panel_do_not_ask
        assert dlg.search_bar.IsEnabled() is False
