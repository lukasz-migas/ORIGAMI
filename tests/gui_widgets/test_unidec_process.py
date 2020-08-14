"""Test UniDec viewer"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.widgets.unidec.panel_process_unidec import PanelProcessUniDec
from origami.widgets.unidec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals
from origami.widgets.unidec.panel_process_unidec_peak_width_tool import PanelPeakWidthTool

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelProcessUniDec(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        icons = Icons()
        dlg = PanelProcessUniDec(None, None, icons)
        dlg.Hide()
        self.wait_for(500)


@pytest.mark.guitest
class TestPanelPeakWidthTool(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelPeakWidthTool(None, None, None)
        dlg.Hide()
        self.wait_for(500)


@pytest.mark.guitest
class TestDialogCustomiseUniDecVisuals(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = DialogCustomiseUniDecVisuals(None)
        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        self.yield_()
