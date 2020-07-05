"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_review_ask import DialogAskReview

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogAskOverride(WidgetTestCase):
    """Test dialog"""

    def test_dialog_overwrite(self):

        dlg = DialogAskReview(self.frame)

        wx.CallLater(250, dlg.review, None)
        res = dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action == "review"
        assert res == wx.ID_SAVE

    def test_dialog_merge(self):

        dlg = DialogAskReview(self.frame)

        wx.CallLater(250, dlg.ok, None)
        res = dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action == "continue"
        assert res == wx.ID_YES

    def test_dialog_cancel(self):

        dlg = DialogAskReview(self.frame)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action is None
        assert res == wx.ID_NO
