"""Test batch apply CCS"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.widgets.ccs.dialog_batch_apply_ccs import DialogBatchApplyCCSCalibration


def get_data():
    """Get test data"""
    return [["Item 1", "Data 1", 500, 1, "TEST1"], ["Item 2", "Data 2", 750, "", "TEST2"]]


@pytest.mark.guitest
class TestDialogBatchApplyCCSCalibration(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        item_list = get_data()

        dlg = DialogBatchApplyCCSCalibration(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(checked) == dlg.n_rows
        assert len(dlg.output_list) == 1

        self.sim_listctrl_select_evt(dlg.peaklist, 0, [dlg.on_select_item])
        assert dlg.charge_value.GetValue() == 1
        assert dlg.mz_value.GetValue() == "500.0000"

        self.sim_listctrl_select_evt(dlg.peaklist, 1, [dlg.on_select_item])
        assert dlg.charge_value.GetValue() == 0
        assert dlg.mz_value.GetValue() == "750.0000"

        # self.sim_textctrl_click_evt(dlg.charge_value, 3, [dlg.on_edit_item])
        # item_info = dlg.on_get_item_information(1)
        # assert item_info["charge"] == 3

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogBatchApplyCCSCalibration(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        self.yield_()

        assert len(dlg.output_list) == 0
