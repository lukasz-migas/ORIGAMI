"""Test Comparison panel"""
# Third-party imports
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.widgets.annotations.panel_annotation_editor import PanelAnnotationEditorUI

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelAnnotationEditorUI(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ["mass_spectrum", "chromatogram", "mobilogram", "heatmap"])
    def test_panel_create(self, plot_type):
        icons = Icons()
        _ = PanelAnnotationEditorUI(None, icons, plot_type)
