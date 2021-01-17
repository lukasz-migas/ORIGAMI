# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.icons.assets import Icons
from origami.icons.assets import Colormaps
from origami.icons.assets import Images
from origami.icons.assets import Bullets


@pytest.mark.guitest
class TestBullets(WidgetTestCase):
    def test_init(self):
        bullets = Bullets()
        assert len(bullets.image_names) > 0
        assert bullets.image_list.GetImageCount() > 0
        assert bullets.image_list.GetImageCount() == len(bullets.image_names)

        # try access
        for value in bullets.image_names:
            assert isinstance(bullets[value], int)
            assert isinstance(getattr(bullets, value), int)
            assert value in dir(bullets)

        with pytest.raises(ValueError):
            Bullets(path="NOT A PATH")


@pytest.mark.guitest
class TestIcons(WidgetTestCase):
    def test_n_icons(self):
        self.icons = Icons()
        assert self.icons.n_icons > 0
        assert self.icons.n_icons == len(self.icons._filelist)

        icon = self.icons.load_ico()
        assert isinstance(icon, wx.Icon)

        with pytest.raises(ValueError):
            Icons(path="NOT A PATH")

    def test_keys(self):
        self.icons = Icons()
        for key in self.icons.keys():
            assert isinstance(key, str)
            assert isinstance(self.icons[key], wx.Bitmap)
            assert isinstance(getattr(self.icons, key), wx.Bitmap)
            assert key in dir(self.icons)

        v = self.icons["NOT A KET"]
        assert v is None

    def test_values(self):
        self.icons = Icons()
        for value in self.icons.values():
            assert isinstance(value, wx.Bitmap)

    def test_items(self):
        self.icons = Icons()
        for key, value in self.icons.items():
            assert isinstance(key, str)
            assert isinstance(value, wx.Bitmap)


@pytest.mark.guitest
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


@pytest.mark.guitest
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
