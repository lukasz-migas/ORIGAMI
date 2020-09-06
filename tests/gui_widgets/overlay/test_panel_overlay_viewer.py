"""Test overlay viewer"""
# Third-party imports
import pytest

# Local imports
from origami.widgets.overlay.panel_overlay_viewer import PanelOverlayViewer

from ...wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelOverlayViewer(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelOverlayViewer(None, None, debug=True)
        dlg.Hide()
        self.wait_for(500)
        assert dlg
