"""Test helper functions"""
import pytest

# Local imports
import wx

# from origami.icons.icons import IconContainer
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
