"""Popup window for filtering table"""
# Standard library imports
from typing import Dict

# Third-party imports

# Local imports
from origami.gui_elements.popup import PopupBase
from origami.gui_elements._panel import TestPanel  # noqa


class PopupTableFilter(PopupBase):
    """Create popup window to filter table"""

    def __init__(self, parent, filter_kwargs: Dict):
        super(PopupTableFilter, self).__init__(parent)

    def make_panel(self):
        """Make popup window"""


# class TestPopup(TestPanel):
#     """Test the popup window"""
#
#     def __init__(self, parent):
#         super().__init__(parent)
#
#         self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)
#
#     def on_popup(self, evt):
#         """Activate popup"""
#         from origami.objects.containers import MobilogramObject
#         import numpy as np
#
#         obj = MobilogramObject(np.arange(100), np.arange(100))
#         p = PopupTableFilter(self, obj=obj)
#         p.position_on_event(evt)
#         p.Show()
#
#
# def _main_popup():
#
#     app = wx.App()
#
#     dlg = TestPopup(None)
#     wx.PostEvent(dlg.btn_1, wx.PyCommandEvent(wx.EVT_BUTTON.typeId, dlg.btn_1.GetId()))
#     dlg.Show()
#
#     app.MainLoop()
#
#
# if __name__ == "__main__":
#     _main_popup()
