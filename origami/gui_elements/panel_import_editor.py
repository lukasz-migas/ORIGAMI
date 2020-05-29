from typing import Dict

from origami.styles import MiniFrame, make_bitmap_btn
import wx
from origami.config.config import CONFIG
from origami.icons.assets import Icons


class PanelModifyItem(MiniFrame):
    def __init__(self, parent, table_dict: Dict, **kwargs):
        MiniFrame.__init__(
            self,
            kwargs.pop("alt_parent", parent),
            title="Modify parameters...",
            style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER,
        )
        self.TABLE_DICT = table_dict

        self._icons = Icons()
        self.make_gui()

    def make_panel(self, *args):
        panel = wx.Panel(self, -1, size=(-1, -1), name="info")

        sizer = wx.BoxSizer(wx.VERTICAL)
        for table_index, table_item in self.TABLE_DICT.items():
            item_sizer = wx.BoxSizer(wx.HORIZONTAL)
            item_text = wx.StaticText(panel, wx.ID_ANY, table_item["name"], size=(60, -1))
            item_sizer.AddSpacer(5)
            item_sizer.Add(item_text)
            item_sizer.AddSpacer(10)
            item_value = wx.TextCtrl(panel, wx.ID_ANY, "")
            item_sizer.Add(item_value)
            item_sizer.AddSpacer(5)
            sizer.Add(item_sizer, flag=wx.EXPAND, border=10)

        previous_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons["previous"])
        ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 26))
        next_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons["next"])

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(previous_btn)
        btn_sizer.Add(ok_btn)
        btn_sizer.Add(next_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer, 1, flag=wx.ALIGN_CENTER_HORIZONTAL, border=10)
        main_sizer.AddSpacer(10)
        main_sizer.Add(btn_sizer, 0, flag=wx.ALIGN_CENTER_HORIZONTAL, border=5)
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel


def main():
    TABLE_DICT = {
        0: {"name": "", "tag": "check", "type": "bool", "order": 0, "id": wx.NewIdRef(), "show": True, "width": 20},
        1: {
            "name": "filename",
            "tag": "filename",
            "type": "str",
            "order": 1,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
        2: {"name": "path", "tag": "path", "type": "str", "order": 2, "id": wx.NewIdRef(), "show": True, "width": 220},
        3: {
            "name": "variable",
            "tag": "variable",
            "type": "float",
            "order": 3,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        4: {
            "name": "m/z range",
            "tag": "mz_range",
            "type": "str",
            "order": 4,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        5: {
            "name": "# scans",
            "tag": "n_scans",
            "type": "str",
            "order": 5,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 55,
        },
        6: {
            "name": "scan range",
            "tag": "scan_range",
            "type": "str",
            "order": 6,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        7: {
            "name": "IM",
            "tag": "ion_mobility",
            "type": "str",
            "order": 7,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 40,
        },
    }

    app = wx.App()
    ex = PanelModifyItem(None, TABLE_DICT)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
