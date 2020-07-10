"""Test statusbar widget"""
# Third-party imports
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.icons.assets import Icons
from origami.gui_elements.statusbar import Statusbar


@pytest.mark.guitest
class TestPanelProcessMassSpectrum(WidgetTestCase):
    """Test dialog"""

    def test_setup(self):
        icons = Icons()
        statusbar = Statusbar(self.frame, icons)
        self.frame.SetStatusBar(statusbar)

        # check interval
        statusbar.update_interval(500)

        # set message
        statusbar.set_message("HELLO", 0)
        assert statusbar.GetStatusText(0) == "HELLO"

        self.frame.Show()
