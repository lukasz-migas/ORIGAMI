"""Basic test panel that can be subclassed to enable unit testing"""
# Third-party imports
import wx


class TestPanel(wx.Dialog):
    """Test panel"""

    btn_1 = None
    btn_2 = None

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="TEST DIALOG")

        self.btn_1 = wx.Button(self, -1, "Do action 1", (25, 50))
        self.btn_2 = wx.Button(self, -1, "Do action 2", (25, 50))

        sizer = wx.BoxSizer()
        sizer.Add(self.btn_1)
        sizer.Add(self.btn_2)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 20)

        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.CenterOnScreen()
        self.Show()
