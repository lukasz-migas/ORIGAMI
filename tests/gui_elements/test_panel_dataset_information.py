"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.panel_dataset_information import PanelDatasetInformation

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelDatasetInformation(WidgetTestCase):
    """Test dialog"""

    def test_panel_init(self):

        dlg = PanelDatasetInformation(self.frame, None, None, debug=True)
        dlg.Show()
