"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_rename import DialogRenameObject

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogDialogRenameObject(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogRenameObject(self.frame, "Test name")
        assert dlg.new_name == "Test name"
        assert dlg.new_name_value.GetBackgroundColour() == wx.WHITE

        # update name and set it to forbidden value
        dlg.new_name_value.SetValue("")
        assert dlg.new_name_value.GetBackgroundColour() != wx.WHITE
        assert "This name is not allowed" in dlg.note_value.GetLabel()

        # update name
        dlg.new_name_value.SetValue("Hello from Test World")

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.new_name == "Hello from Test World"

    def test_dialog_cancel(self):

        dlg = DialogRenameObject(self.frame, "Test name")

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.new_name is None
