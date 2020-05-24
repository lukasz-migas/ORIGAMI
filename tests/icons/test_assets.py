# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons


class TestIcons:
    @classmethod
    def setup_class(cls):
        _ = wx.App()
        cls.icons = Icons()

    def test_n_icons(self):
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

    def test_keys(self):
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert self.icons[key]

    def test_values(self):
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)
