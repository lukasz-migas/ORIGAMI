"""Test UniDec viewer"""
# Third-party imports
import wx
import pytest

# Local imports
from tests.wxtc import WidgetTestCase
from origami.widgets.unidec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals


@pytest.mark.guitest
class TestDialogCustomiseUniDecVisuals(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = DialogCustomiseUniDecVisuals(None)
        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        self.yield_()
