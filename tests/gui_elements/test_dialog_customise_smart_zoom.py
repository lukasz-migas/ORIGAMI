"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_customise_smart_zoom import DialogCustomiseSmartZoom

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogCustomiseSmartZoom(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = DialogCustomiseSmartZoom(self.frame)
        dlg.smart_zoom_check.SetValue(True)
        assert dlg.smart_zoom_soft_max.IsEnabled() is True

        dlg.smart_zoom_check.SetValue(False)
        dlg.on_toggle_controls(None)
        dlg.on_apply(None)
        assert dlg.smart_zoom_soft_max.IsEnabled() is False

        wx.CallLater(250, dlg.on_ok, wx.ID_OK)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        dlg = DialogCustomiseSmartZoom(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_NO)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()
