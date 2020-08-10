"""Test LESA viewer"""
# Third-party imports
import pytest

# Local imports
from origami.widgets.lesa.panel_imaging_lesa_import import PanelImagingImportDataset

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelImagingImportDataset(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelImagingImportDataset(None, None)
        dlg.Show()

        assert dlg
        self.wait_for(200)
