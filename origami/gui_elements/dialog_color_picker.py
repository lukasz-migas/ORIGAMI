"""Dialog to allow for selection new color"""
# Third-party imports
import wx

# Local imports
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_255_to_1


class DialogColorPicker(wx.ColourDialog):
    """Dialog that allows for selection of new color"""

    def __init__(self, parent, colors):
        self.colors = self.GetColours(colors)
        wx.ColourDialog.__init__(self, parent, self.colors)

        # Ensure the full colour dialog is displayed,
        # not the abbreviated version.
        self.GetColourData().SetChooseFull(True)
        self.CentreOnParent()

    def ShowModal(self):
        """ Simplified ShowModal()"""
        return super(DialogColorPicker, self).ShowModal()

    def GetChosenColour(self):  # noqa
        """ Shorthand... """
        data = self.GetColourData()
        color = data.GetColour().Get()
        color_255 = convert_rgb_255_to_1(color)
        font_color = get_font_color(color, return_rgb=True)
        return color, color_255, font_color

    @staticmethod
    def GetColours(colors):  # noqa
        # Restore custom colors
        custom_colors = wx.ColourData()
        for key in colors:
            color = list(colors[key])
            custom_colors.SetCustomColour(key, color)

        return custom_colors

    def GetCustomColours(self):  # noqa
        data = self.GetColourData()
        custom_colors = dict()
        for i in range(16):
            custom_colors[i] = data.GetCustomColour(i)
        return custom_colors


def _main():

    app = wx.App()
    frame = wx.Frame(None, -1)
    ex = DialogColorPicker(frame, [])
    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
