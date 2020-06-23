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
        # dlg.file_delimiter_choice.SetStringSelection("comma")
        # assert CONFIG.saveDelimiterTXT == "comma"
        # assert CONFIG.saveDelimiter == ","
        # assert CONFIG.saveExtension == ".csv"
        # dlg.file_delimiter_choice.SetStringSelection("tab")
        # dlg.on_apply(None)
        # assert CONFIG.saveDelimiterTXT == "tab"
        # assert CONFIG.saveDelimiter == "\t"
        # assert CONFIG.saveExtension == ".txt"
        # dlg.file_delimiter_choice.SetStringSelection("space")
        # dlg.on_apply(None)
        # assert CONFIG.saveDelimiterTXT == "space"
        # assert CONFIG.saveDelimiter == " "
        # assert CONFIG.saveExtension == ".txt"

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
