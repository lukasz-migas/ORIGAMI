"""Module responsible for loading icons from the assets folder"""
# Standard library imports
import os
import glob

# Third-party imports
import wx

# Local imports
from origami.utils.utilities import is_valid_python_name

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")


class Icons:
    def __init__(self, fmt="*.png", path=ASSETS_PATH):
        # determine list of files in the directory
        if not os.path.exists(path):
            raise ValueError("Specified path does not exist")
        self._filelist = glob.glob(os.path.join(path, fmt))
        self.icons = self.load_icons()

    @property
    def n_icons(self):
        return len(self.icons)

    def __getitem__(self, item):
        """Key access to the icon dictionary"""
        return self.icons.get(item, None)

    def __getattr__(self, item):
        # allow access to group members via dot notation
        try:
            return self.icons[item]
        except KeyError:
            raise AttributeError

    def __dir__(self):
        # noinspection PyUnresolvedReferences
        base = super().__dir__()
        keys = sorted(set(base + list(self.icons.keys())))
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


class Example(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Example, self).__init__(*args, **kwargs)

        self.InitUI()

    def InitUI(self):
        icons = Icons()
        print(dir(icons))

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()

        for key, icon in icons.items():
            fileItem = fileMenu.Append(wx.ID_ANY, key, "Quit application")
            fileItem.SetBitmap(icon)
            self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)

        menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        self.SetSize((300, 200))
        self.SetTitle("Simple menu")
        self.Centre()

    def OnQuit(self, e):
        self.Close()


def main():
    app = wx.App()

    ex = Example(None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
