"""Test CCS calibration"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.widgets.ccs.panel_ccs_calibration import PanelCCSCalibration


@pytest.mark.guitest
class TestPanelCCSCalibration(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelCCSCalibration(None, debug=True)
        dlg.Hide()
        self.wait_for(500)
