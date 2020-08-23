"""Test UniDec viewer"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.widgets.unidec.panel_process_unidec_peak_width_tool import PanelPeakWidthTool


@pytest.mark.guitest
class TestPanelPeakWidthTool(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelPeakWidthTool(None, None, None)
        dlg.Hide()
        self.wait_for(500)
