"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_ask_labels import DialogSelectLabels

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogSelectLabels(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogSelectLabels(self.frame)
        x_label, y_label = dlg.get_labels()
        assert dlg.x_label_enter.IsEnabled() is False
        assert dlg.x_label == dlg.x_label_combo.GetStringSelection() == x_label
        assert dlg.y_label_enter.IsEnabled() is False
        assert dlg.y_label == dlg.y_label_combo.GetStringSelection() == y_label

        dlg.x_label_combo.SetStringSelection("Other...")
        dlg.y_label_combo.SetStringSelection("Other...")
        dlg.on_select(None)

        assert dlg.x_label_enter.IsEnabled() is True
        assert dlg.y_label_enter.IsEnabled() is True

        dlg.x_label_enter.SetValue("New Label X")
        dlg.y_label_enter.SetValue("New Label Y")

        wx.CallLater(250, dlg.on_ok, wx.ID_OK)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.x_label == "New Label X"
        assert dlg.y_label == "New Label Y"

    def test_dialog_cancel(self):

        dlg = DialogSelectLabels(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_NO)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.x_label is None
        assert dlg.y_label is None
