"""Utility class for display cards in the UI"""
# Standard library imports
from typing import Dict
from typing import List

# Third-party imports
import wx
import wx.lib.scrolledpanel

# Local imports
from origami.styles import Dialog
from origami.styles import Validator
from origami.utils.system import running_under_pytest
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font


class ItemCard(wx.Panel):
    """Card item"""

    # ui elements
    item_id_label, checkbox_value, title_value, about_value = None, None, None, None

    def __init__(self, parent, item_info: List[Dict] = None):
        super(ItemCard, self).__init__(parent, style=wx.SIMPLE_BORDER)
        self.make_gui()

        if isinstance(item_info, dict):
            self.set_info(**item_info)

    @property
    def is_checked(self) -> bool:
        """Returns flag if item is checked"""
        return self.checkbox_value.GetValue()

    @property
    def item_id(self) -> str:
        """Returns the item id"""
        return self.item_id_label.GetLabel()

    @property
    def title(self) -> str:
        """Returns the title of the object"""
        return self.title_value.GetValue()

    def make_gui(self):
        """Make UI"""
        self.item_id_label = wx.StaticText(self, -1)
        self.checkbox_value = make_checkbox(self, "", tooltip="Export data to Document")

        self.title_value = wx.TextCtrl(self, -1, "", validator=Validator("path"))
        self.title_value.SetMaxLength(200)
        set_tooltip(self.title_value, "Title of the object")

        self.about_value = wx.StaticText(self, -1, size=(-1, -1))
        set_tooltip(self.about_value, "Contents of the object")

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(wx.StaticText(self, -1, "Id:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.item_id_label, (n, 1), (1, 2), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticText(self, -1, "Save:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.checkbox_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(self, -1, "Title:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.title_value, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(self, -1, "Contents:"), (n, 0), flag=wx.ALIGN_TOP | wx.ALIGN_RIGHT)
        grid.Add(self.about_value, (n, 1), (1, 2), flag=wx.EXPAND)
        grid.AddGrowableCol(2, 1)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def set_info(self, item_id: str = "", check: bool = True, title: str = "", about: str = ""):
        """Set information about the object"""
        self.item_id_label.SetLabel(item_id)
        self.checkbox_value.SetValue(check)
        self.title_value.SetValue(title)
        self.about_value.SetLabel(about)


class DialogCardManager(Dialog):
    """Card manager"""

    # ui elements
    ok_btn, cancel_btn = None, None

    REVIEW_MSG = (
        "Please review the list of items shown below and select items which you would like to add to the document."
    )

    def __init__(self, parent, item_list=None):
        Dialog.__init__(self, parent, title="Cards", style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER & ~wx.MAXIMIZE_BOX)

        self.item_list = item_list
        self.cards = []
        self._cancel = False
        self._output_list = []

        self.make_gui()

        self.SetMinSize((800, 500))
        self.Layout()
        self.CenterOnParent()
        self.Show(True)
        self.SetFocus()

    @property
    def output_list(self):
        """Return a list of selected items"""
        if not self._cancel:
            return self._output_list
        return []

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""
        self._output_list.clear()
        self._cancel = True
        super(DialogCardManager, self).on_close(evt, force)

    def on_ok(self, _evt):
        """Gracefully close window"""
        self._output_list = self.get_selected_items()
        super(DialogCardManager, self).on_ok(_evt)

    def get_selected_items(self):
        """Get list of selected items"""
        item_list = []
        for card in self.cards:
            if card.is_checked:
                item_list.append((card.item_id, card.title))
        return item_list

    def make_gui(self):
        """Make and arrange main panel"""

        # make panel
        panel = self.make_panel()
        btn_grid = self.make_buttons()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 5)
        main_sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def make_panel(self):
        """Make panel"""
        panel = wx.lib.scrolledpanel.ScrolledPanel(self, wx.ID_ANY)

        info_label = wx.StaticText(panel, -1, self.REVIEW_MSG)
        info_label.Wrap(300)
        set_item_font(info_label)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(info_label, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        main_sizer.AddSpacer(5)

        for item in self.item_list:
            card = ItemCard(panel, item)
            self.cards.append(card)
            main_sizer.Add(card, 0, wx.EXPAND | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        # it = self._sizer.Detach(1)
        # it = self._sizer.Detach(5)
        # self._sizer.Layout()
        # self._sizer.Insert(1, card, 0, wx.EXPAND | wx.ALL, 2)

        if not running_under_pytest():
            panel.SetupScrolling()

        return panel

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Select", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER)

        return btn_grid


def _main():
    # Local imports
    from origami.app import App

    app = App()

    item_list = [
        {"item_id": "1231231233", "title": "Title", "about": "LINE 1"},
        {"item_id": "31245", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "5235252344", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "312312313", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3"},
        {"item_id": "1231412321", "title": "Title", "about": "LINE 1\nLINE 2\nLINE 3\nLINE 1\nLINE 2\nLINE 3"},
    ]

    ex = DialogCardManager(None, item_list)

    ex.Show()
    app.MainLoop()
    print(ex.output_list)


if __name__ == "__main__":
    _main()
