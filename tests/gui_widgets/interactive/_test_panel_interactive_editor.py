"""Test overlay viewer"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.utils.secret import get_short_hash
from origami.widgets.interactive.panel_interactive_editor import PanelInteractiveEditor


def _get_item_list():
    item_list = [
        ["MassSpectra/Summed Spectrum", "Title", get_short_hash()],
        ["MassSpectra/rt=0-15", "Title", get_short_hash()],
        ["MassSpectra/rt=41-42", "Title", get_short_hash()],
        ["Chromatograms/Summed Chromatogram", "Title", get_short_hash()],
        ["Mobilogram/Summed Chromatogram", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title2", get_short_hash()],
    ]
    return item_list


@pytest.mark.guitest
class TestPanelInteractiveEditor(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        item_list = _get_item_list()
        dlg = PanelInteractiveEditor(None, None, item_list=item_list, debug=True)
        dlg.Show()
        self.wait_for(500)
