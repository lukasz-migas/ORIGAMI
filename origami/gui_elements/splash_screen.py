"""Splash screen"""
import wx
import wx.adv
from wx.adv import SplashScreen

from origami.icons.assets import Images


class SplashScreenView(SplashScreen):
    def __init__(self, timeout: int = 3000):
        bmp = Images().logo
        SplashScreen.__init__(self, bmp, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, timeout, None, -1)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # self.fc = wx.CallLater(1000, self.ShowMain)

    def on_close(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()
