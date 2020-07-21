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
        _ = PanelImagingImportDataset(None, None)
