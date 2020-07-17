"""Test Comparison panel"""
# Third-party imports
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.widgets.mz_picker.panel_peak_picker import PanelPeakPicker

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelPeakPicker(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        icons = Icons()
        _ = PanelPeakPicker(None, None, icons, debug=True)
