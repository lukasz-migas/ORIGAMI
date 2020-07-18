"""Test LESA viewer"""
# Third-party imports
import pytest

# Local imports
from origami.widgets.manual.panel_manual_import import PanelManualImportDataset

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelManualImportDataset(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("activation_type", ("CIU", "SID"))
    def test_panel_create(self, activation_type):
        dlg = PanelManualImportDataset(None, None, activation_type=activation_type)

        assert dlg.activation_type_choice.GetStringSelection() == activation_type
