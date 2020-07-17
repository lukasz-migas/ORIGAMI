"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.panel_process_msdt import PanelProcessMSDT

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelProcessMSDT(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessMSDT(self.frame, None)
        dlg.Show()
