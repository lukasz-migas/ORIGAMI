# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.dialog_multi_directory_picker import DialogMultiDirPicker


def get_data():
    """Get test data"""
    return (
        "D:\\TEST.origami",
        [
            "Chromatograms",
            "Configs",
            "IonHeatmaps",
            "MassSpectra",
            "Metadata",
            "Mobilograms",
            "MSDTHeatmaps",
            "Output",
            "Overlays",
            "Raw",
            "Tandem",
        ],
        [
            {"id": 0, "select": True, "check": True, "filename": "Chromatograms", "path": "D:\\TEST.origami"},
            {"id": 1, "select": True, "check": True, "filename": "Chromatograms", "path": "D:\\TEST.origami"},
            {"id": 2, "select": True, "check": True, "filename": "Chromatograms", "path": "D:\\TEST.origami"},
        ],
    )


@pytest.mark.guitest
class TestDialogMultiDirPicker(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = DialogMultiDirPicker(self.frame)

        wx.CallLater(250, dlg.on_ok, wx.ID_OK)
        dlg.ShowModal()
        self.yield_()

    def test_dialog_cancel(self):
        dlg = DialogMultiDirPicker(self.frame)

        wx.CallLater(250, dlg.on_close, wx.ID_CLOSE)
        dlg.ShowModal()
        self.yield_()
