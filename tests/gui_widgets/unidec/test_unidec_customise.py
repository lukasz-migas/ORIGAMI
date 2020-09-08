"""Test UniDec viewer"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.widgets.unidec.panel_unidec_visuals import PanelCustomiseUniDecVisuals


@pytest.mark.guitest
class TestPanelCustomiseUniDecVisuals(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelCustomiseUniDecVisuals(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)
