# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons

from ..wxtc import WidgetTestCase


class TestIcons(WidgetTestCase):
    def test_n_icons(self):
        self.icons = Icons()
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

    def test_keys(self):
        self.icons = Icons()
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert self.icons[key]

    def test_values(self):
        self.icons = Icons()
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        self.icons = Icons()
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)
