"""Test helper functions"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_spin_ctrl_int
from origami.gui_elements.helpers import make_spin_ctrl_double

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestHelpers(WidgetTestCase):
    """Test dialog"""

    def test_spin_ctrl_double(self):
        panel = wx.Panel(self.frame, wx.ID_ANY)
        # icons = IconContainer()

        control = make_spin_ctrl_double(panel, 3, 100, 200, 0.5)
        assert isinstance(control, wx.SpinCtrlDouble)

        control = make_spin_ctrl_int(panel, 0, 0, 100)
        assert isinstance(control, wx.SpinCtrl)

        control = make_checkbox(panel, "")
        assert isinstance(control, wx.CheckBox)
