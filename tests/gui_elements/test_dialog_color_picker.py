"""Test color picker"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.dialog_color_picker import DialogColorPicker


@pytest.mark.guitest
class TestDialogColorPicker(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = DialogColorPicker(self.frame, [])
        result = dlg.GetChosenColour()
        assert len(result) == 3

        wx.CallLater(250, dlg.Close)
        dlg.Show()
        self.yield_()

    def test_dialog_cancel(self):
        dlg = DialogColorPicker(self.frame, [])

        wx.CallLater(250, dlg.Close)
        dlg.Show()
        self.yield_()
