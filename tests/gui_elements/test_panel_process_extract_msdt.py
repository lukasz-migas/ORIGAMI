"""Test PanelProcessExtractMSDT dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_process_extract_msdt import PanelProcessExtractMSDT


@pytest.mark.guitest
class TestPanelProcessExtractMSDT(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessExtractMSDT(self.frame, None)
        dlg.Show()
