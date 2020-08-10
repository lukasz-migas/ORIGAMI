"""Test Comparison panel"""
# Third-party imports
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.widgets.annotations.panel_annotation_editor import PanelAnnotationEditor

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelAnnotationEditorUI(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ["mass_spectrum", "chromatogram", "mobilogram", "heatmap", "ms_heatmap"])
    def test_panel_create(self, plot_type):
        icons = Icons()
        dlg = PanelAnnotationEditor(None, None, icons, plot_type)
        dlg.Show()
        assert dlg
        self.wait_for(500)
