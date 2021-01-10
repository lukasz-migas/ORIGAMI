"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_data_import import PanelDatasetImport
from origami.config.config import USERS


@pytest.mark.guitest
class TestPanelDatasetInformation(WidgetTestCase):
    """Test dialog"""

    def test_panel_init(self):

        dlg = PanelDatasetImport(self.frame, None, None, debug=True)
        dlg.Hide()

        # test few methods
        dlg.on_import_dataset("DATASET PATH")
        dlg.on_update_output(None)

        # update user list
        USERS.add_user("NAME", "EMAIL", "INSTITUTION")
        dlg.on_update_user_list()
