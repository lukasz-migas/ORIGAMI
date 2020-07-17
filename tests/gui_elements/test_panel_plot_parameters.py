"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.panel_plot_parameters import PanelVisualisationSettingsEditor

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelVisualisationSettingsEditor(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        _ = PanelVisualisationSettingsEditor(self.frame, None)
