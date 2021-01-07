"""Test plot settings panels"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.widgets.interactive.panel_plot_parameters import PanelVisualisationSettingsEditor


@pytest.mark.guitest
class TestPanelVisualisationSettingsEditor(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelVisualisationSettingsEditor(self.frame, None)
