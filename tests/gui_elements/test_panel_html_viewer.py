"""Test PanelAbout dialog"""
# Standard library imports
import sys

# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_html_viewer import PanelHTMLViewer


@pytest.mark.guitest
@pytest.mark.skipif(sys.platform == "win32", reason="Running this test under Windows can sporadically cause errors")
class TestPanelHTMLViewer(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelHTMLViewer(self.frame, link="www.google.com")
