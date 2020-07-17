"""Test Comparison panel"""
# Third-party imports
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.widgets.comparison.panel_signal_comparison_viewer import PanelSignalComparisonViewer

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelSignalComparisonViewer(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        icons = Icons()
        _ = PanelSignalComparisonViewer(None, None, icons, "", None, None, debug=True)
