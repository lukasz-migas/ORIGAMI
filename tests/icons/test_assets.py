# Third-party imports
import wx

# Local imports
from origami.utils.test import WidgetTestCase
from origami.icons.assets import Icons
from origami.icons.assets import Colormaps
from origami.icons.assets import Images
from origami.icons.assets import Bullets


class TestBullets(WidgetTestCase):
    def test_init(self):
        self.bullets = Bullets()
        assert len(self.bullets.image_names) > 0
        assert len(self.bullets.image_list) > 0


class TestIcons(WidgetTestCase):
    def test_n_icons(self):
        self.icons = Icons()
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

    def test_keys(self):
        self.icons = Icons()
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert isinstance(self.icons[key], wx.Bitmap)

    def test_values(self):
        self.icons = Icons()
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        self.icons = Icons()
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)


class TestColormaps(WidgetTestCase):
    def test_n_icons(self):
        self.icons = Colormaps()
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

    def test_keys(self):
        self.icons = Colormaps()
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert isinstance(self.icons[key], wx.Bitmap)

    def test_values(self):
        self.icons = Colormaps()
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        self.icons = Colormaps()
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)


class TestImages(WidgetTestCase):
    def test_n_icons(self):
        self.icons = Images()
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

    def test_keys(self):
        self.icons = Images()
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert isinstance(self.icons[key], wx.Bitmap)

    def test_values(self):
        self.icons = Images()
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        self.icons = Images()
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)
