"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_review_cards import DialogCardManager

from ..wxtc import WidgetTestCase


def get_data():
    """Get test data"""
    item_list = [
        {"item_id": "1231231233", "title": "Title", "about": "LINE 1"},
        {"item_id": "31245", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "5235252344", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "312312313", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "1231412321", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3\nLINE 1\nLINE 2\nLINE 3"},
    ]
    return item_list


@pytest.mark.guitest
class TestDialogCardManager(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        item_list = get_data()

        dlg = DialogCardManager(self.frame, item_list)
        checked = dlg.get_selected_items()
        assert len(item_list) == len(checked)

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        assert len(dlg.output_list) == len(item_list) == len(checked)
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogCardManager(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        self.yield_()

        assert len(dlg.output_list) == 0
