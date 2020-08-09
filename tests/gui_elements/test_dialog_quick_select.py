"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_quick_select import DialogQuickSelection

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestDialogQuickSelection(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("options", (["Option 1", "Option 2"], ["1", "2", "3"]))
    def test_dialog_create(self, options):

        dlg = DialogQuickSelection(self.frame, options)

        assert dlg.options == options
        assert dlg.value is None

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        dlg.Destroy()
        self.yield_()

        assert dlg.value == options[0]
