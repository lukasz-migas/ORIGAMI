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

    def test_panel_create(self, get_env_with_document):
        # get environment
        env = get_env_with_document
        document = env.on_get_document()

        document_title = document.title
        dataset_name = "MassSpectra/Summed Spectrum"
        # instantiate icons
        icons = Icons()

        # setup peak picker
        dlg = PanelPeakPicker(None, None, icons, document_title=document_title, dataset_name=dataset_name, debug=True)

        # change method
        dlg.preprocess_check.SetValue(False)
        dlg.on_set_method("native_local")
        dlg.on_find_peaks(None)
        dlg.on_set_method("small_molecule")
        dlg.on_find_peaks(None)
        dlg.on_set_method("native_differential")
        dlg.on_find_peaks(None)

        self.wait_for(200)
