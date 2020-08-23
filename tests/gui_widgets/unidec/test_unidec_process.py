"""Test UniDec viewer"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.icons.assets import Icons
from origami.widgets.unidec.panel_process_unidec import PanelProcessUniDec


@pytest.mark.guitest
class TestPanelProcessUniDec(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        icons = Icons()
        dlg = PanelProcessUniDec(None, None, icons, debug=True)
        dlg.Hide()
        self.wait_for(500)
