"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.dialog_quick_select import DialogQuickSelection


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
        self.yield_()

        assert dlg.value == options[0]

    @pytest.mark.parametrize("options", (["Option 1", "Option 2"], ["1", "2", "3"]))
    def test_dialog_close(self, options):

        dlg = DialogQuickSelection(self.frame, options)

        assert dlg.options == options
        assert dlg.value is None

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.value is None

    @pytest.mark.parametrize("options", (["Option 1", "Option 2"], ["1", "2", "3"]))
    def test_dialog_sim(self, options):

        dlg = DialogQuickSelection(self.frame, options)

        assert dlg.options == options
        assert dlg.value is None

        for option in options:
            self.sim_combobox_click_evt(dlg.choice_value, option, [dlg.on_apply])
            assert dlg.value == option

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.value is None
