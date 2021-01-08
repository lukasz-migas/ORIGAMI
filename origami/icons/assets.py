"""Module responsible for loading icons from the assets folder"""
# Standard library imports
import os
import glob

# Third-party imports
import wx

# Local imports
from origami.utils.utilities import is_valid_python_name

BASE_PATH = os.path.dirname(__file__)
ASSETS_PATH = os.path.join(BASE_PATH, "icons")
COLORMAPS_PATH = os.path.join(BASE_PATH, "colormaps")
IMAGES_PATH = os.path.join(BASE_PATH, "images")
BULLETS_PATH = os.path.join(BASE_PATH, "bullets")


class Icons:
    """Simple loader of .png icons from the file system"""

    def __init__(self, fmt="*.png", path=ASSETS_PATH):
        # determine list of files in the directory
        if not os.path.exists(path):
            raise ValueError("Specified path does not exist")
        self._filelist = glob.glob(os.path.join(path, fmt))
        self.icons = self.load_icons()

    @property
    def n_icons(self):
        """Return the number of icons in the folder"""
        return len(self.icons)

    def __getitem__(self, item):
        """Key access to the icon dictionary"""
        return self.icons.get(item, None)

    def __getattr__(self, item):
        # allow access to group members via dot notation
        try:
            return self.icons.get(item, None)
        except KeyError:
            return self.icons.get("blank")

    # noinspection PyUnresolvedReferences
    def __dir__(self):
        base = super().__dir__()
        keys = sorted(set(base + list(self.icons.keys())))  # noqa
        keys = [k for k in keys if is_valid_python_name(k)]
        return keys

    def keys(self):
        """Returns names of the icons"""
        return self.icons.keys()

    def values(self):
        """Returns icon values"""
        return self.icons.values()

    def items(self):
        """Returns iterable of key : icon"""
        return self.icons.items()

    def load_icons(self):
        """Loads icons in the directory and places them inside container"""
        icons = dict()
        for path in self._filelist:
            filename = os.path.splitext(os.path.split(path)[1])[0]
            icons[filename] = wx.Bitmap(path)
        return icons

    @staticmethod
    def load_ico():
        """Load .ico icon"""
        ico_path = os.path.join(BASE_PATH, "icon.ico")
        assert os.path.exists(ico_path), "Icon path does not exist"
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(ico_path, wx.BITMAP_TYPE_ANY))
        return icon


class Colormaps(Icons):
    """Loader of colormap images"""

    def __init__(self, fmt="*.png", path=COLORMAPS_PATH):
        super(Colormaps, self).__init__(fmt, path)


class Images(Icons):
    """Loader of images"""

    def __init__(self, fmt="*.png", path=IMAGES_PATH):
        super(Images, self).__init__(fmt, path)


class Bullets:
    """Loader of bullets"""

    def __init__(self, fmt="*.png", path=BULLETS_PATH):
        if not os.path.exists(path):
            raise ValueError("Specified path does not exist")
        self._filelist = glob.glob(os.path.join(path, fmt))

        self.image_names = dict()
        self.image_list = wx.ImageList(13, 13)
        self.load()

    def __getitem__(self, item):
        """Key access to the icon dictionary"""
        return self.image_names.get(item, None)

    def __getattr__(self, item):
        # allow access to group members via dot notation
        return self.image_names[item]

    # noinspection PyUnresolvedReferences
    def __dir__(self):
        base = super().__dir__()
        keys = sorted(set(base + list(self.image_names.keys())))  # noqa
        keys = [k for k in keys if is_valid_python_name(k)]
        return keys

    def load(self):
        """Load data"""
        for i, path in enumerate(self._filelist):
            filename = os.path.splitext(os.path.split(path)[1])[0]
            self.image_list.Add(wx.Bitmap(path))
            self.image_names[filename] = i


if __name__ == "__main__":

    def _main():
        from origami.app import App

        # noinspection DuplicatedCode
        class Example(wx.Frame):
            """Example app"""

            def __init__(self, *args, **kwargs):
                super(Example, self).__init__(*args, **kwargs)

                self.init()

            def init(self):
                """"Initialize menu"""
                menubar = wx.MenuBar()

                icons = Icons()
                menu_file = wx.Menu()
                for i, (key, icon) in enumerate(icons.items()):
                    file_item = menu_file.Append(wx.ID_ANY, key, "Quit application")
                    file_item.SetBitmap(icon)
                    self.Bind(wx.EVT_MENU, self.on_close, file_item)
                    if i % 25 == 0:
                        menu_file.Break()
                menubar.Append(menu_file, "&Icons")

                colormaps = Colormaps()
                menu_cmap = wx.Menu()
                for i, (key, icon) in enumerate(colormaps.items()):
                    file_item = menu_cmap.Append(wx.ID_ANY, key, "Quit application")
                    file_item.SetBitmap(icon)
                    self.Bind(wx.EVT_MENU, self.on_close, file_item)
                    if i % 25 == 0:
                        menu_cmap.Break()
                menubar.Append(menu_cmap, "&Colormaps")

                images = Images()
                menu_images = wx.Menu()
                for i, (key, icon) in enumerate(images.items()):
                    file_item = menu_images.Append(wx.ID_ANY, key, "Quit application")
                    file_item.SetBitmap(icon)
                    self.Bind(wx.EVT_MENU, self.on_close, file_item)
                    if i % 25 == 0:
                        menu_images.Break()
                menubar.Append(menu_images, "&Images")

                self.SetMenuBar(menubar)

                self.SetSize((300, 200))
                self.SetTitle("Simple menu")
                self.Centre()

            def on_close(self, e):
                """Close application"""
                self.Close()

        app = App()

        ex = Example(None)
        ex.Show()
        app.MainLoop()

    _main()
