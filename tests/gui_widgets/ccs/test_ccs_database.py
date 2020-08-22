"""Test UniDec viewer"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.widgets.ccs.panel_ccs_database import PanelCCSDatabase


@pytest.mark.guitest
class TestPanelCCSDatabase(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelCCSDatabase(None)
        dlg.Hide()
        self.wait_for(500)
