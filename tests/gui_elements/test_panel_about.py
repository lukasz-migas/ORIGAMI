"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_about import PanelAbout


@pytest.mark.guitest
class TestPanelAbout(WidgetTestCase):
    """Test dialog"""

    def test_dialog_close(self):

        dlg = PanelAbout(self.frame)
        dlg.Show()
