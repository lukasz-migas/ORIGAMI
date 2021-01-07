"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations


@pytest.mark.guitest
class TestDialogCustomiseUserAnnotations(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogCustomiseUserAnnotations(self.frame)

        wx.CallLater(250, dlg.on_ok, wx.ID_OK)
        dlg.ShowModal()
        self.yield_()

    def test_dialog_cancel(self):

        dlg = DialogCustomiseUserAnnotations(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_NO)
        dlg.ShowModal()
        self.yield_()
