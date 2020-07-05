"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogCustomiseUserAnnotations(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogCustomiseUserAnnotations(self.frame)

        wx.CallLater(250, dlg.on_ok, wx.ID_OK)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):

        dlg = DialogCustomiseUserAnnotations(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_NO)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()
