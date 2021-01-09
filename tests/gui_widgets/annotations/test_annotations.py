"""Test Comparison panel"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.icons.assets import Icons
from origami.widgets.annotations.panel_annotation_editor import PanelAnnotationEditor
from origami.widgets.annotations.popup_annotations_settings import PopupAnnotationSettings


@pytest.mark.guitest
class TestPanelAnnotationEditorUI(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ["mass_spectrum", "chromatogram", "mobilogram", "heatmap", "ms_heatmap"])
    def test_panel_create(self, plot_type):
        icons = Icons()
        dlg = PanelAnnotationEditor(None, None, icons, plot_type)
        dlg.Hide()
        self.wait_for(500)
        assert dlg


@pytest.mark.guitest
class TestPopupAnnotationSettings(WidgetTestCase):
    def test_init(self):
        popup = PopupAnnotationSettings(None)
        popup.Show()
        self.wait_for(200)
        assert popup
