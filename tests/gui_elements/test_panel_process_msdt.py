"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_process_msdt import PanelProcessMSDT


@pytest.mark.guitest
class TestPanelProcessMSDT(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessMSDT(self.frame, None)
        dlg.Show()
