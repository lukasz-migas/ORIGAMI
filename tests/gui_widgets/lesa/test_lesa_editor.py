"""Test LESA viewer"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.widgets.lesa.panel_imaging_lesa import PanelImagingLESAViewer


@pytest.mark.guitest
class TestPanelImagingLESAViewer(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelImagingLESAViewer(None, None, debug=True)
        dlg.Hide()
        self.wait_for(500)
