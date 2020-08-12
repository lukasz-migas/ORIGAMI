"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.icons.icons import IconContainer
from origami.gui_elements.panel_about import PanelAbout

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelAbout(WidgetTestCase):
    """Test dialog"""

    def test_dialog_close(self):
        icons = IconContainer()

        dlg = PanelAbout(self.frame, icons)
        dlg.Show()
