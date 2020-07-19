"""Test PanelProcessExtractMSDT dialog"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.panel_process_extract_msdt import PanelProcessExtractMSDT

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelProcessExtractMSDT(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessExtractMSDT(self.frame, None)
        dlg.Show()
