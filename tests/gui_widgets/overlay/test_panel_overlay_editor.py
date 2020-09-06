"""Test overlay viewer"""
# Third-party imports
import pytest

# Local imports
from origami.utils.secret import get_short_hash
from origami.widgets.overlay.panel_overlay_editor import PanelOverlayEditor

from ...wxtc import WidgetTestCase


def _get_item_list():
    item_list = [
        ["MassSpectra/Summed Spectrum", "Title", "(1000,)", "TEST\n\n\nTEST", None, get_short_hash()],
        ["MassSpectra/rt=0-15", "Title", "(1000,)", "", 0, get_short_hash()],
        ["MassSpectra/rt=41-42", "Title", "(1000,)", "label ", 0, get_short_hash()],
        ["Chromatograms/Summed Chromatogram", "Title", "(513,)", "", 0, get_short_hash()],
        ["Mobilograms/Summed Mobilogram", "Title", "(200,)", "", 0, get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title", "(200, 500)", "label 3", 0, get_short_hash()],
    ]
    return item_list


@pytest.mark.guitest
class TestPanelOverlayEditor(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        item_list = _get_item_list()
        dlg = PanelOverlayEditor(None, None, item_list=item_list, debug=True)
        dlg.Hide()

        # check number of rows
        assert dlg.n_rows == 3  # number of mass spec rows
        self.sim_combobox_click_evt(dlg.overlay_1d_spectrum_type, "Chromatograms", [dlg.on_populate_item_list])
        assert dlg.n_rows == 1  # number of chromatograms
        self.sim_combobox_click_evt(dlg.overlay_1d_spectrum_type, "Mobilograms", [dlg.on_populate_item_list])
        assert dlg.n_rows == 1  # number of chromatograms

        self.wait_for(500)
