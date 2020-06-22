"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_ask import KEYWORDS
from origami.gui_elements.dialog_ask import DialogAsk

from ..wxtc import WidgetTestCase


class TestDialogAsk(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("keyword", KEYWORDS)
    def test_dialog_ok(self, keyword):

        dlg = DialogAsk(self.frame, keyword=keyword)
        dlg.input_value.SetValue(1)

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        if dlg.item_validator == "integer":
            assert dlg.return_value == 1
            assert isinstance(dlg.return_value, int)
        else:
            assert dlg.return_value == 1.0
            assert isinstance(dlg.return_value, float)

    @pytest.mark.parametrize("keyword", KEYWORDS)
    def test_dialog_cancel(self, keyword):

        dlg = DialogAsk(self.frame, keyword=keyword)

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()
