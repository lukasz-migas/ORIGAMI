"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.dialog_ask_override import DialogAskOverride

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogAskOverride(WidgetTestCase):
    """Test dialog"""

    def test_dialog_overwrite(self):

        dlg = DialogAskOverride(self.frame)

        wx.CallLater(250, dlg.overwrite, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action == CONFIG.import_duplicate_panel_action == "override"

    def test_dialog_merge(self):

        dlg = DialogAskOverride(self.frame)

        wx.CallLater(250, dlg.merge, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action == CONFIG.import_duplicate_panel_action == "merge"

    def test_dialog_copy(self):

        dlg = DialogAskOverride(self.frame)

        wx.CallLater(250, dlg.create_copy, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action == CONFIG.import_duplicate_panel_action == "duplicate"

    def test_dialog_cancel(self):

        dlg = DialogAskOverride(self.frame)

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.action is None
        assert CONFIG.import_duplicate_panel_action is None
