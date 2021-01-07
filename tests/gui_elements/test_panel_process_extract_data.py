"""Test PanelProcessExtractData dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_process_extract_data import PanelProcessExtractData


@pytest.mark.guitest
class TestPanelProcessExtractData(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessExtractData(self.frame, None)
        dlg.Show()
