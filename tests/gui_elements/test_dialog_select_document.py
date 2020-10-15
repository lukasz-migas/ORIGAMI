"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_users import DialogAddUser

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogAddUser(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = DialogAddUser(None)

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        self.yield_()

    def test_dialog_cancel(self):
        dlg = DialogAddUser(None)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        self.yield_()
