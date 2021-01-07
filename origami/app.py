# Third-party imports
import wx


class App(wx.App):
    """Slightly modified wxApp"""

    def InitLocale(self):
        """Initialize locale"""
        self.ResetLocale()
