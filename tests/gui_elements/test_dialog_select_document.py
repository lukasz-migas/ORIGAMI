"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_select_document import DialogSelectDocument

from ..wxtc import WidgetTestCase


def get_data():
    """Get test data for the dialog"""
    document_list = ["Document 1", "Document 2"]
    return document_list


class TestDialogSelectDocument(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("allow_new_document", (True, False))
    def test_dialog_ok(self, allow_new_document):
        document_list = get_data()

        dlg = DialogSelectDocument(self.frame, document_list=document_list, allow_new_document=allow_new_document)
        assert dlg.add_btn.IsEnabled() is allow_new_document

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.current_document is not None

    @pytest.mark.parametrize("allow_new_document", (True, False))
    def test_dialog_cancel(self, allow_new_document):
        document_list = get_data()

        dlg = DialogSelectDocument(self.frame, document_list=document_list, allow_new_document=allow_new_document)
        assert dlg.add_btn.IsEnabled() is allow_new_document

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.current_document is None
