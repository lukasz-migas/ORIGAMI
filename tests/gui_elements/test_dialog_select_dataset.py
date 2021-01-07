"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.dialog_select_dataset import DialogSelectDataset


def get_data():
    """Get test data for the dialog"""
    document_list = ["TEST", "TEST2"]
    dataset_list = dict(TEST=["Spectrum 1", "Spectrum 2"], TEST2=["Spec 3"])
    return document_list, dataset_list


@pytest.mark.guitest
class TestDialogSelectDataset(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        document_list, dataset_list = get_data()

        dlg = DialogSelectDataset(self.frame, document_list, dataset_list)
        assert dlg.document is None
        assert dlg.dataset is None
        assert dlg._document_list == document_list
        assert dlg._dataset_list == dataset_list

        wx.CallLater(250, dlg.document_list_choice.Select, 1)
        wx.CallLater(350, dlg.on_make_selection, wx.ID_OK)
        wx.CallLater(450, dlg.on_close, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.document is not None
        assert dlg.dataset is not None

    def test_dialog_cancel(self):
        document_list, dataset_list = get_data()

        dlg = DialogSelectDataset(self.frame, document_list, dataset_list)
        assert dlg.document is None
        assert dlg.dataset is None
        assert dlg._document_list == document_list
        assert dlg._dataset_list == dataset_list

        wx.CallLater(250, dlg.on_close, wx.ID_CANCEL)
        dlg.ShowModal()
        self.yield_()

        assert dlg.document is None
        assert dlg.dataset is None
