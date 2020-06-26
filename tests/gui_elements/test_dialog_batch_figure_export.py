"""Test DialogExportData dialog"""
# Standard library imports
import os

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.dialog_batch_figure_exporter import DialogExportFigures

from ..wxtc import WidgetTestCase


class TestDialogExportData(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):

        dlg = DialogExportFigures(self.frame)
        dlg.folder_path.SetValue(os.getcwd())
        assert CONFIG.image_folder_path == dlg.folder_path.GetValue()

        # ensure apply works
        dlg.file_format_choice.SetStringSelection("svg")
        dlg.on_apply(None)
        assert CONFIG.imageFormat == "svg"

        # check conversions work correctly
        dlg.width_cm_value.SetValue(2.54)
        dlg.height_cm_value.SetValue(25.4)
        dlg.on_apply_size_cm(None)
        assert dlg.width_inch_value.GetValue() == 1
        assert dlg.height_inch_value.GetValue() == 10

        dlg.width_inch_value.SetValue(10)
        dlg.height_inch_value.SetValue(2.54)
        dlg.on_apply_size_cm(None)
        assert dlg.width_cm_value.GetValue() == 2.54
        assert dlg.height_cm_value.GetValue() == 25.4

        # check toggles work
        dlg.image_resize_check.SetValue(False)
        dlg.on_toggle_controls(None)
        assert not dlg.left_export_value.IsEnabled()
        assert not dlg.bottom_export_value.IsEnabled()
        assert not dlg.width_export_value.IsEnabled()
        assert not dlg.height_export_value.IsEnabled()
        assert not dlg.width_inch_value.IsEnabled()
        assert not dlg.height_inch_value.IsEnabled()
        assert not dlg.width_cm_value.IsEnabled()
        assert not dlg.height_cm_value.IsEnabled()

        dlg.image_resize_check.SetValue(True)
        dlg.on_toggle_controls(None)
        assert dlg.left_export_value.IsEnabled()
        assert dlg.bottom_export_value.IsEnabled()
        assert dlg.width_export_value.IsEnabled()
        assert dlg.height_export_value.IsEnabled()
        assert dlg.width_inch_value.IsEnabled()
        assert dlg.height_inch_value.IsEnabled()
        assert dlg.width_cm_value.IsEnabled()
        assert dlg.height_cm_value.IsEnabled()

        wx.CallLater(250, dlg.on_save, wx.ID_OK)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):

        dlg = DialogExportFigures(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_NO)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()
