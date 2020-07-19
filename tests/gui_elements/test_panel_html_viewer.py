"""Test PanelAbout dialog"""
# Local imports
import sys

import pytest

from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
@pytest.mark.skipif(sys.platform == "win32", reason="Running this test under Windows can sporadically cause errors")
class TestPanelHTMLViewer(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelHTMLViewer(self.frame, link="www.google.com")
