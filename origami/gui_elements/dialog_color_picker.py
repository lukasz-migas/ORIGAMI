import wx
from utils.color import convertRGB255to1, determineFontColor


class DialogColorPicker(wx.ColourDialog):

    def __init__(self, parent, colors):
        self.colors = self.GetColours(colors)

        wx.ColourDialog.__init__(self, parent, self.colors)

        # Ensure the full colour dialog is displayed,
        # not the abbreviated version.
        self.GetColourData().SetChooseFull(True)
        self.CentreOnParent()

    def ShowModal(self):
        """ Simplified ShowModal(), returning strings 'ok' or 'cancel'. """
        result = wx.ColourDialog.ShowModal(self)
        if result == wx.ID_OK:
            return 'ok'
        else:
            return 'cancel'

    def GetChosenColour(self):
        """ Shorthand... """
        data = self.GetColourData()
        color = data.GetColour().Get()
        color_255 = convertRGB255to1(color)
        font_color = determineFontColor(color, return_rgb=True)
        return color, color_255, font_color

    @staticmethod
    def GetColours(colors):
        # Restore custom colors
        custom_colors = wx.ColourData()
        for key in colors:
            color = list(colors[key])
            custom_colors.SetCustomColour(key, color)

        return custom_colors

    def GetCustomColours(self):
        data = self.GetColourData()
        custom_colors = dict()
        for i in range(16):
            custom_colors[i] = data.GetCustomColour(i)
        return custom_colors
