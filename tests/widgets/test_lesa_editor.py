"""Test LESA viewer"""
# Third-party imports
import pytest

# Local imports
from origami.widgets.lesa.panel_imaging_lesa import PanelImagingLESAViewer

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelImagingLESAViewer(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        _ = PanelImagingLESAViewer(None, None, debug=True)
