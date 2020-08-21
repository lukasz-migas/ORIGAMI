"""Annotations settings popup"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.popup import PopupBase
from origami.gui_elements._panel import TestPanel  # noqa
from origami.gui_elements.helpers import make_checkbox


class PopupAnnotationSettings(PopupBase):
    """Create popup window to modify few uncommon settings"""

    highlight_on_selection = None
    zoom_on_selection = None
    zoom_window_size = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        PopupBase.__init__(self, parent, style)

    def make_panel(self):
        """Make popup window"""
        self.highlight_on_selection = make_checkbox(self, "")
        self.highlight_on_selection.SetValue(CONFIG.annotate_panel_highlight)
        self.highlight_on_selection.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.zoom_on_selection = make_checkbox(self, "")
        self.zoom_on_selection.SetValue(CONFIG.annotate_panel_zoom_in)
        self.zoom_on_selection.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.zoom_on_selection.Bind(wx.EVT_CHECKBOX, self.on_toggle)

        self.zoom_window_size = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.annotate_panel_zoom_in_window),
            min=0.0001,
            max=250,
            initial=CONFIG.annotate_panel_zoom_in_window,
            inc=25,
            size=(90, -1),
        )
        self.zoom_window_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(wx.StaticText(self, -1, "highlight:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.highlight_on_selection, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "zoom-in:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_on_selection, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "window size:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_window_size, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.set_info(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()

    def on_apply(self, evt):
        """Update settings"""
        CONFIG.annotate_panel_highlight = self.highlight_on_selection.GetValue()
        CONFIG.annotate_panel_zoom_in = self.zoom_on_selection.GetValue()
        CONFIG.annotate_panel_zoom_in_window = float(self.zoom_window_size.GetValue())

        if evt is not None:
            evt.Skip()

    def on_toggle(self, evt):
        """Update UI elements"""
        self.zoom_window_size.Enable(not CONFIG.annotate_panel_zoom_in)

        if evt is not None:
            evt.Skip()


class TestPopup(TestPanel):
    """Test the popup window"""

    def __init__(self, parent):
        super().__init__(parent)

        self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

    def on_popup(self, evt):
        """Activate popup"""

        p = PopupAnnotationSettings(self)
        p.position_on_window(self)
        p.Show()


def _main_popup():

    app = wx.App()

    dlg = TestPopup(None)
    wx.PostEvent(dlg.btn_1, wx.PyCommandEvent(wx.EVT_BUTTON.typeId, dlg.btn_1.GetId()))
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main_popup()
