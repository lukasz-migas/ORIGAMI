"""Test DialogBatchDataExtract"""
import pytest
import wx

from origami.gui_elements.dialog_batch_data_extract import DialogBatchDataExtract
from tests.wxtc import WidgetTestCase


def get_data():
    """Get test data"""
    return [["Item 1", "Data 1", "Data 1"], ["Item 2", "Data 2", "Data 2"]]


@pytest.mark.guitest
class TestDialogBatchDataExtract(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogBatchDataExtract(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogBatchDataExtract(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0
