"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_notify_open_documents import DialogNotifyOpenDocuments

from ..wxtc import WidgetTestCase


class TestDialogNotifyOpenDocuments(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):

        dlg = DialogNotifyOpenDocuments(self.frame, msg)
        if msg is None:
            assert dlg.message is not None
        else:
            assert dlg.message == msg

        assert dlg.FindFocus() == dlg.cancel_btn

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_save(self, msg):

        dlg = DialogNotifyOpenDocuments(self.frame, msg)
        if msg is None:
            assert dlg.message is not None
        else:
            assert dlg.message == msg

        wx.CallLater(250, dlg.on_save_documents, None)
        res = dlg.ShowModal()
        assert res == wx.ID_SAVE
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):

        dlg = DialogNotifyOpenDocuments(self.frame)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()
