"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_save_unsaved import DialogSaveUnsaved

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogSaveUnsaved(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogSaveUnsaved(self.frame, "Document 1", "MassSpectra/Summed Spectrum")
        assert dlg.new_name == "Summed Spectrum"
        assert dlg.group_name == "MassSpectra"
        assert dlg.new_name_value.GetBackgroundColour() != wx.WHITE

        dlg.new_name_value.SetValue("Another name")
        assert dlg.new_name_value.GetBackgroundColour() == wx.WHITE

        # update name and set it to forbidden value
        dlg.new_name_value.SetValue("")
        assert dlg.new_name_value.GetBackgroundColour() != wx.WHITE
        assert "This name is not allowed" in dlg.note_value.GetLabel()

        dlg.new_name_value.SetValue("Another name")
        assert dlg.new_name_value.GetBackgroundColour() == wx.WHITE

        # update name and set it to forbidden value
        dlg.new_name_value.SetValue("Summed Spectrum")
        assert dlg.new_name_value.GetBackgroundColour() != wx.WHITE
        assert "This name is not allowed" in dlg.note_value.GetLabel()

        # update name
        dlg.new_name_value.SetValue("Summed Spectrum 2")

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.new_name == "MassSpectra/Summed Spectrum 2"

    def test_dialog_cancel(self):

        dlg = DialogSaveUnsaved(self.frame, "Document 1", "MassSpectra/Summed Spectrum")

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.new_name is None
